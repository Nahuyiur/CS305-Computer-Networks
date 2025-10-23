import threading
import socket
import time
import pickle
from collections import OrderedDict
from queue import Queue, Empty
from dnslib import DNSRecord, QTYPE, RR, A, CNAME, DNSHeader, TXT
from dns import resolver, rdatatype, name as dns_name


class CacheManager:
    """
    --- Task 2. Automatic Cache Saving and Loading ---

    This class is responsible for managing all cache operations in the DNS server. It not only implements efficient in-memory caching,
    but also supports persisting the cache to a disk file, enabling state recovery after server restarts.

    Core features include:
    - Thread-safe design, ensuring data consistency under high-concurrency environments.
    - Automatic expiration based on TTL (Time to Live).
    - LRU (Least Recently Used) eviction policy, automatically removing the least recently accessed entries when the cache is full.
    - Automatically loading the cache file on server startup and saving it on shutdown.
    """

    def __init__(self, cache_file='dns_cache.pkl', max_size=200):
        """
        Initialize a CacheManager instance.

        This constructor sets the path and maximum capacity of the cache file,
        and immediately attempts to call `_load_from_file` to load existing cache from disk.
        """
        self.cache_file = cache_file
        self.max_size = max_size
        self.cache = self._load_from_file()
        self.lock = threading.Lock()

    def _load_from_file(self):
        """
        --- Task 2.1 Load Cache from File ---

        At server startup, load and initialize the cache from a disk file.

        This method attempts to open the specified cache file and deserialize its data using pickle.
        Upon successful loading, it iterates through all cache entries and precisely removes any records
        that have expired during the server's downtime, based on their stored expiration timestamps,
        ensuring only valid cache entries are loaded into memory.

        :return:
            - collections.OrderedDict: If loading succeeds, returns an ordered dictionary containing valid cache entries.
            - collections.OrderedDict: If the file does not exist, is empty, or corrupted, returns a new empty ordered dictionary.
        """
        try:
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
                current_time = time.time()
                valid_cache = OrderedDict()
                
                # 过滤掉过期的缓存条目
                for key, (record, expire_time) in cache_data.items():
                    if expire_time > current_time:
                        valid_cache[key] = (record, expire_time)
                
                return valid_cache
        except (FileNotFoundError, EOFError, pickle.PickleError):
            return OrderedDict()

    def save_to_file(self):
        """
        --- Task 2.2 Save Cache to File ---

        Persist all current in-memory cache entries to a disk file.

        This method is typically called when the server shuts down normally. It locks the cache,
        then uses pickle to serialize the entire in-memory `self.cache` ordered dictionary
        and writes it completely to the designated cache file.

        :return:
            - None: This function does not return a value.
        """
        with self.lock:
            try:
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(dict(self.cache), f)
            except Exception as e:
                print(f"Failed to save cache: {e}")

    def readCache(self, domain_name, qtype_str):
        """
        --- Task 2.3 Read Cache & Task 2.5 TTL (partial implementation) ---

        Retrieve a DNS record from the in-memory cache based on domain name and query type.

        This method is the core logic for reading from the cache. It first checks whether the requested record exists.
        If it does, it performs a critical TTL check: comparing the current time with the stored expiration timestamp.
        If the record has not expired, it returns the record; otherwise, it deletes the entry from the cache and returns None,
        triggering a new network query.

        :param domain_name: (str) The domain name being queried.
        :param qtype_str: (str) The record type being queried (e.g., "A", "CNAME").

        :return:
            - dnslib.DNSRecord: If a valid, unexpired cached record is found, return the record object.
            - None: If no such record exists in the cache or the record has expired, return None.
        """
        with self.lock:
            key = f"{domain_name}:{qtype_str}"
            if key in self.cache:
                record, expire_time = self.cache[key]
                current_time = time.time()
                if expire_time > current_time:
                    # 更新LRU顺序
                    self.cache.move_to_end(key)
                    return record
                else:
                    # 删除过期条目
                    del self.cache[key]
            return None

    def writeCache(self, domain_name, qtype_str, response_record):
        """
        --- Task 2.4 Write Cache & Task 2.5 TTL (partial implementation) ---

        Write a new DNS query result into the in-memory cache.

        This method is the core logic for writing to the cache. It first calculates the TTL from the DNS response
        and combines it with the current time to generate an absolute future "expiration timestamp". Then,
        it stores the DNS response record along with this timestamp as a unit in the cache. This method also handles
        negative caching (setting a fixed TTL for NXDOMAIN) and enforces the LRU eviction policy.

        :param domain_name: (str) The domain name that was queried.
        :param qtype_str: (str) The type of the queried record.
        :param response_record: (dnslib.DNSRecord) The complete DNS response object containing the data to be cached.

        :return:
            - None: This function does not return a value.
        """
        with self.lock:
            key = f"{domain_name}:{qtype_str}"
            current_time = time.time()
            
            # 根据响应类型设置TTL
            if response_record.header.rcode == 3:  # NXDOMAIN
                ttl = 60  # NXDOMAIN的TTL为60秒
            else:
                ttl = 300  # 其他响应的TTL为300秒
                
                # 尝试从响应记录中获取实际TTL
                for rr in response_record.rr:
                    if hasattr(rr, 'ttl') and rr.ttl > 0:
                        ttl = min(rr.ttl, 300)  # 限制最大TTL为300秒
                        break
            
            expire_time = current_time + ttl
            
            # 如果缓存已满，删除最旧的条目
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            
            self.cache[key] = (response_record, expire_time)


# --- Add method to ReplyGenerator for generating redirect responses ---
class ReplyGenerator:
    """This class is used to generate various DNS response packets."""

    @staticmethod
    def replyForNotFound(income_record):
        header = DNSHeader(id=income_record.header.id, qr=1, rcode=3)
        record = DNSRecord(header, q=income_record.q)
        return record

    @staticmethod
    def myReply(income_record, rr_list):
        response = DNSRecord(DNSHeader(id=income_record.header.id, qr=1, ra=1), q=income_record.q)
        for rr in rr_list:
            response.add_answer(rr)
        return response

    @staticmethod
    def replyForRedirect(income_record, redirect_ip, ttl=300):
        """
        --- Task 3.2 DNS Redirection (Response Construction) ---

        Construct a custom DNS response packet for DNS redirection functionality.

        When the server decides to redirect a domain name request to another IP address,
        this method generates a DNS response containing a "forged" A record. This response tells the client
        that the IP address corresponding to the queried domain is our specified `redirect_ip`.

        :param income_record: (dnslib.DNSRecord) The original DNS query request sent by the client.
                              We use it to retrieve the request ID and question section to ensure
                              the response can be correctly recognized by the client.
        :param redirect_ip: (str) The target IPv4 address to which the original domain should be redirected.
        :param ttl: (int, optional) The Time-To-Live for this forged A record, in seconds. Defaults to 300.
        :return:
            - dnslib.DNSRecord: A fully constructed DNS response object whose answer section
                                contains an A record pointing to `redirect_ip`.
        """
        header = DNSHeader(id=income_record.header.id, qr=1, ra=1)
        response = DNSRecord(header, q=income_record.q)
        
        # 创建A记录指向重定向IP
        a_record = A(income_record.q.qname, ttl, redirect_ip)
        response.add_answer(a_record)
        
        return response

    @staticmethod
    def replyForBlocked(income_record, reason="Blocked due to security policy"):
        """
        --- Task 3.3 DNS Filtering (Response Construction) ---

        Construct a custom DNS response packet to explicitly refuse a query for a blocked domain.

        Instead of simply pretending the domain does not exist (NXDOMAIN), this method
        generates a response with a "Refused" status code (RCODE 5). This accurately
        informs the client that the query was intentionally denied due to a policy,
        which is a more precise and informative way to handle filtering.
        Optionally, it can include a TXT record to provide a human-readable reason for the block.

        :param income_record: (dnslib.DNSRecord) The original DNS query request sent by the client.
                              This is used to match the transaction ID and question section.
        :param reason: (str, optional) The reason for the block, which will be embedded in a
                                     TXT record in the answer section. If None, no TXT record is added.
        :return:
            - dnslib.DNSRecord: A DNS response object with a 'Refused' status code.
        """
        header = DNSHeader(id=income_record.header.id, qr=1, rcode=5)  # RCODE 5 = REFUSED
        response = DNSRecord(header, q=income_record.q)
        
        # 添加TXT记录说明阻止原因
        if reason:
            txt_record = TXT(income_record.q.qname, 300, reason)
            response.add_answer(txt_record)
        
        return response


class DNSServer:
    """
    --- Task 1.2 DNSServer Implementation ---
    This class serves as the central coordinator of the entire DNS server, acting like an "air traffic controller".
    It does not perform the complex logic of DNS resolution itself, but instead manages the server's lifecycle,
    including startup, receiving client requests, dispatching tasks to worker threads (DNSHandler),
    collecting results, and sending final responses back to clients.

    To achieve high performance and concurrency, this class employs the classic multi-threaded "producer-consumer" model.
    """

    def __init__(self, source_ip, source_port, ip='127.0.0.1', port=5533, num_workers=20):
        """
        Initialize a DNSServer instance.

        This method sets up basic server configurations such as listening IP and port,
        creates the main socket required for network communication, and prepares the infrastructure for multi-threading.
        """
        self.source_ip = source_ip
        self.source_port = source_port
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 初始化缓存管理器
        self.cache_manager = CacheManager()
        
        # 初始化队列和线程控制
        self.request_queue = Queue()
        self.response_queue = Queue()
        self.workers = []
        self.num_workers = num_workers
        self.running = False
        self.receiver_thread = None
        self.sender_thread = None

    def start(self):
        """
        Start the full service of the DNS server.

        This method brings the server into active state, including binding the port, starting all background threads
        (receiver, sender, worker pool), and keeping the main thread waiting for shutdown signals.
        """
        try:
            # 绑定端口
            self.socket.bind((self.ip, self.port))
            print(f"DNS Server started on {self.ip}:{self.port}")
            print(f"Source IP: {self.source_ip}, Source Port: {self.source_port}")
            
            self.running = True
            
            # 启动工作线程
            for i in range(self.num_workers):
                worker = DNSHandler(self.source_ip, self.source_port, self.cache_manager, 
                                  self.request_queue, self.response_queue, i)
                worker.daemon = True
                worker.start()
                self.workers.append(worker)
            
            # 启动接收线程
            self.receiver_thread = threading.Thread(target=self._receive_loop)
            self.receiver_thread.daemon = True
            self.receiver_thread.start()
            
            # 启动发送线程
            self.sender_thread = threading.Thread(target=self._send_loop)
            self.sender_thread.daemon = True
            self.sender_thread.start()
            
            print(f"DNS Server is running with {self.num_workers} workers")
            
            # 主线程等待
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down DNS Server...")
                self.stop()
                
        except Exception as e:
            print(f"Failed to start DNS Server: {e}")
            self.stop()

    def stop(self):
        """
        --- Task 1.2 stop method ---
        Gracefully shut down the server and perform necessary cleanup.
        """
        print("Stopping DNS Server...")
        self.running = False
        
        # 保存缓存
        self.cache_manager.save_to_file()
        
        # 关闭socket
        if self.socket:
            self.socket.close()
        
        print("DNS Server stopped")

    def _receive_loop(self):
        """
        --- Task 1.2 Receive Messages ---
        This method runs in a separate "receiver" thread, solely responsible for listening on the network port.
        """
        print("Receiver thread started")
        while self.running:
            try:
                data, address = self.socket.recvfrom(512)
                print(f"Received query from {address}, size: {len(data)}")
                self.request_queue.put((data, address))
            except Exception as e:
                if self.running:
                    print(f"Error receiving data: {e}")
                break

    def _send_loop(self):
        """
        --- Task 1.2 Send Messages ---
        This method runs in a separate "sender" thread, solely responsible for sending responses.
        """
        while self.running:
            try:
                address, response_data = self.response_queue.get(timeout=1)
                self.socket.sendto(response_data, address)
            except Empty:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error sending data: {e}")
                break


class DNSHandler(threading.Thread):
    def __init__(self, source_ip, source_port, cache_manager, request_queue, response_queue, worker_id):
        super().__init__()
        self.source_ip = source_ip
        self.source_port = source_port
        self.BOOTSTRAP_DNS_SERVERS = ['223.5.5.5', '119.29.29.29', '180.76.76.76', '8.8.8.8', '1.1.1.1']
        self.cache_manager = cache_manager
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.worker_id = worker_id
        self.root_server_cache = self._initialize_root_server()

        # ==============================================================================
        # --- Example: DNS Redirection and Filtering Rules ---
        # ==============================================================================

        # --- 1. DNS Redirection Rules (redirect_map) ---
        #    This dictionary defines domains that should be "hijacked" and their target IP addresses.
        #    Key (key): The domain to match (lowercase, without trailing dot).
        #    Value (value): The IPv4 address string to return.
        self.redirect_map = {
            # Example 1: Redirect all queries for google.com to localhost (127.0.0.1).
            #           Often used for development or complete service blocking.
            "www.google.com": "127.0.0.1",
            "google.com": "127.0.0.1",

            # Example 2: Redirect a common ad-tracking domain to "0.0.0.0".
            #           "0.0.0.0" is an invalid, non-routable address.
            #           Clients will fail to connect, effectively blocking ads.
            "doubleclick.net": "0.0.0.0",
            "www.google-analytics.com": "0.0.0.0",

            # Example 3: "Friendly" redirection, e.g., map a memorable short domain to an IP.
            #           (for demonstration only)
            "friendly.name": "8.8.8.8"
        }

        # --- 2. DNS Filtering Rules (blocklist) ---
        #    This set defines domains to be completely blocked (blacklist).
        #    For any domain in this list, the server returns NXDOMAIN (domain does not exist).
        #    Using a set instead of a list provides O(1) lookup speed.
        self.blocklist = {
            # Example 1: Block known malware or phishing site domains.
            "malware-site.com",
            "phishing-attack.net",

            # Example 2: Block intrusive ad or tracking servers.
            "ads.annoying-tracker.com",
            "stats.unwanted-data-miner.org",

            # Example 3: Block specific sites you don't want users to access.
            "distracting-social-media.com"
        }
        # --- End of DNS Redirection and Filtering Rule Definitions ---
        # ==============================================================================

    def _initialize_root_server(self):
        try:
            server_ip, _ = self.queryRoot(self.source_ip, self.source_port)
            print(f"Worker {self.worker_id} initialized with root IP: {server_ip}")
            return server_ip
        except Exception as e:
            print(f"Worker {self.worker_id} failed to init root server: {e}. Falling back to 198.41.0.4.")
            return '198.41.0.4'

    def run(self):
        while True:
            try:
                message, address = self.request_queue.get()
                response_record = self.handle(message)
                if response_record:
                    self.response_queue.put((address, response_record.pack()))
            except Exception as e:
                print(f"Worker {self.worker_id} error: {e}")
                pass

    def handle(self, message):
        """Handle a single DNS query, incorporating filtering and redirection logic."""
        try:
            income_record = DNSRecord.parse(message)
            domain_name = str(income_record.q.qname).strip('.')
            qtype_str = QTYPE[income_record.q.qtype]
            print(f"Handling query for {domain_name} ({qtype_str})")

            # ==============================================================================
            # --- Task 3.2 DNS Redirection Logic ---
            # After filtering, check if redirection is needed.
            # If the domain is in our redirect map, immediately build a response pointing to the new IP.
            # ==============================================================================
            if domain_name in self.redirect_map:
                redirect_ip = self.redirect_map[domain_name]
                print(f"Redirecting {domain_name} to {redirect_ip}")
                return ReplyGenerator.replyForRedirect(income_record, redirect_ip)

            # --- Task 3.2 END ---
            # ==============================================================================

            # ==============================================================================
            # --- Task 3.3 DNS Filtering Logic ---
            # This is where filtering is enforced. It runs before any other operation for maximum efficiency.
            # If the domain is in our blacklist, we immediately return a "does not exist" response.
            # ==============================================================================
            if domain_name in self.blocklist:
                return ReplyGenerator.replyForBlocked(income_record)

            # --- Task 3.3 END ---
            # ==============================================================================

            # ==============================================================================
            # --- Task 1.3 Core DNS Resolution Process ---
            # If the domain is neither filtered nor redirected, proceed with standard resolution.
            # This follows the strategy: "check cache first, then perform network query".
            # ==============================================================================
            # 首先检查缓存
            cached_response = self.cache_manager.readCache(domain_name, qtype_str)
            if cached_response:
                return cached_response
            
            # 缓存未命中，进行网络查询
            rr_list = self.query(domain_name, income_record.q.qtype)
            if rr_list:
                response = ReplyGenerator.myReply(income_record, rr_list)
                # 将结果写入缓存
                self.cache_manager.writeCache(domain_name, qtype_str, response)
                return response
            else:
                # 查询失败，返回NXDOMAIN
                return ReplyGenerator.replyForNotFound(income_record)

            # --- Task 1.3 END ---
            # ==============================================================================

        except Exception as e:
            print(f"Error in handle: {e}")
            try:
                return ReplyGenerator.replyForNotFound(DNSRecord.parse(message))
            except:
                return None

    def query(self, query_name, qtype):
        """
        --- Task 1.5 Iterative Query Implementation ---
        This method is the core resolution engine of the local DNS server. When a query cannot be found in the cache,
        this method simulates a DNS client's behavior, starting from the root server, following the DNS hierarchy,
        and progressively "asking for directions" until it finds the authoritative DNS server responsible for the domain
        and obtains the final answer.

        :param query_name: (str) The domain name to resolve, e.g., "www.google.com".
        :param qtype: (int) The record type to query, e.g., dnslib.QTYPE.A.

        :return:
            - list: On success, returns a list of one or more dnslib.RR objects.
                    This list may include CNAME and final A records.
            - None: On failure (due to non-existent domain, timeout, or error), returns None.
        """
        try:
            # 创建查询请求
            query = DNSRecord.question(query_name, qtype)
            query.header.rd = 0  # 设置为迭代查询
            
            # 从根服务器开始查询
            current_server = self.root_server_cache
            
            # 迭代查询过程
            for level in range(10):  # 最多10级查询，防止无限循环
                # 发送查询到当前服务器
                response = self._send_query(query, current_server)
                if not response:
                    return None
                
                # 检查响应
                if response.header.rcode != 0:  # 有错误
                    return None
                
                # 检查是否有答案
                if response.rr:
                    # 处理CNAME记录
                    cname_rrs = [rr for rr in response.rr if rr.rtype == QTYPE.CNAME]
                    a_rrs = [rr for rr in response.rr if rr.rtype == QTYPE.A]
                    
                    if cname_rrs:
                        # 有CNAME记录，需要继续查询CNAME目标
                        cname_target = str(cname_rrs[0].rdata)
                        result = cname_rrs + a_rrs
                        
                        # 如果CNAME目标没有A记录，需要查询CNAME目标
                        if not a_rrs:
                            cname_query = DNSRecord.question(cname_target, QTYPE.A)
                            cname_query.header.rd = 0
                            cname_response = self._send_query(cname_query, current_server)
                            if cname_response and cname_response.rr:
                                result.extend([rr for rr in cname_response.rr if rr.rtype == QTYPE.A])
                        
                        return result
                    else:
                        # 直接返回A记录
                        return a_rrs
                
                # 没有答案，查找权威服务器
                authority_rrs = [rr for rr in response.auth if rr.rtype == QTYPE.NS]
                if not authority_rrs:
                    return None
                
                # 获取权威服务器的IP地址
                ns_name = str(authority_rrs[0].rdata)
                ns_ip = self._get_ns_ip(ns_name, current_server)
                if not ns_ip:
                    # 尝试从additional记录中获取NS服务器的IP
                    if hasattr(response, 'ar') and response.ar:
                        for rr in response.ar:
                            if rr.rtype == QTYPE.A and str(rr.rname) == ns_name:
                                ns_ip = str(rr.rdata)
                                break
                    if not ns_ip:
                        return None
                
                current_server = ns_ip
                
        except Exception as e:
            print(f"Query error: {e}")
            return None

    def queryRoot(self, source_ip, source_port):
        """
        --- Task 1.4 Robust Dynamic Discovery of Root Server IP ---

        Dynamically and reliably discover the IP address of a currently available root DNS server.

        The iterative DNS query of a local DNS server must start from a root server. However, root server IPs may change
        or become inaccessible due to DNS pollution. This method queries a preset list of reliable public DNS servers
        to dynamically obtain a valid root server IP, serving as the "starting point" for all subsequent queries.

        :param source_ip: (str) Source IP address to use for this bootstrap query.
        :param source_port: (int) Source port to use for this bootstrap query.

        :return:
            - tuple: On success, returns (root_ip, root_ns_name), where:
                - root_ip (str): IPv4 address of a root server.
                - root_ns_name (str): Domain name of that root server.

        :raises Exception: If none of the preset public DNS servers can return a root server IP.
        """
        for dns_server in self.BOOTSTRAP_DNS_SERVERS:
            try:
                # 查询根服务器列表
                query = DNSRecord.question(".", QTYPE.NS)
                query.header.rd = 1  # 递归查询
                
                response = self._send_query(query, dns_server)
                if response and response.rr:
                    # 获取第一个根服务器的IP
                    root_ns = str(response.rr[0].rdata)
                    root_ip = self._get_ns_ip(root_ns, dns_server)
                    if root_ip:
                        return root_ip, root_ns
            except Exception as e:
                continue
        
        raise Exception("Failed to get root server IP from any bootstrap DNS server")
    
    def _send_query(self, query, server_ip, timeout=5):
        """发送DNS查询到指定服务器"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.bind((self.source_ip, 0))
            
            sock.sendto(query.pack(), (server_ip, 53))
            data, _ = sock.recvfrom(512)
            sock.close()
            
            return DNSRecord.parse(data)
        except Exception as e:
            return None
    
    def _get_ns_ip(self, ns_name, current_server):
        """获取名称服务器的IP地址"""
        try:
            # 查询A记录
            query = DNSRecord.question(ns_name, QTYPE.A)
            query.header.rd = 0
            response = self._send_query(query, current_server)
            
            if response and response.rr:
                for rr in response.rr:
                    if rr.rtype == QTYPE.A:
                        return str(rr.rdata)
            
            # 如果A记录查询失败，尝试从additional记录中获取
            if hasattr(response, 'ar') and response.ar:
                for rr in response.ar:
                    if rr.rtype == QTYPE.A:
                        return str(rr.rdata)
            
            return None
        except Exception:
            return None


def get_local_ip():
    """
    --- Task 1.1 Automatically Detect Outbound Interface IP ---
    When performing network communication, especially on machines with multiple interfaces (Ethernet, Wi-Fi, VPN),
    the program needs to know which IP to use as the source so that response packets are correctly routed back.
    This function aims to automatically discover this "best" outbound IP address.

    :return:
        - str: On success, returns the local IP address as a string (e.g., '192.168.1.100').
        - str: On failure (e.g., no network, firewall), returns a robust fallback '0.0.0.0'.
    """
    try:
        # 创建一个临时socket连接到外部地址来获取本地IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 连接到Google DNS服务器（不实际发送数据）
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception:
        # 如果上述方法失败，尝试获取主机名对应的IP
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip.startswith("127."):
                # 如果是回环地址，尝试其他方法
                return '0.0.0.0'
            return local_ip
        except Exception:
            return '0.0.0.0'


if __name__ == '__main__':
    source_ip = get_local_ip()
    print(f"Automatically detected local IP address: {source_ip}")
    local_dns_server = DNSServer(source_ip, source_port=0, num_workers=20)
    local_dns_server.start()