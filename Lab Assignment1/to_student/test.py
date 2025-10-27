import subprocess
import threading
import time
from collections import defaultdict

# (DOMAINS_TO_TEST list remains unchanged)
DOMAINS_TO_TEST = [
    # 1. Major domestic tech giants, widely use CNAME and CDN; fast resolution, ideal for verifying CNAME handling capability.
    "www.baidu.com",

    # 2. Another major domestic company, also heavily uses CNAME and CDN, serves as a core functionality test case.
    "www.taobao.com",

    # 3. Well-known Chinese university website, typically uses simple A records with short resolution chains, good for testing basic A record queries.
    "www.tsinghua.edu.cn",

    # 4. High-traffic video platform with complex CDN configurations, excellent for testing the server's ability to handle complex responses.
    "www.bilibili.com",

    # 5. Mainstream news portal, stable network and reliable resolution.
    "www.sina.com.cn",

    # Redirection and filtering test domains
    "www.google.com",
    "www.google-analytics.com",
    "ads.annoying-tracker.com"
]

# DOMAINS_TO_TEST = [
#     # ==============================================================================
#     # --- Category 1: Normal Resolution Test Cases (A Records & CNAME Chains) ---
#     # ==============================================================================
    
#     # 1.1 Major domestic tech giants with CNAME and CDN
#     "www.baidu.com",           # Baidu - complex CNAME chain, CDN
#     "www.taobao.com",          # Taobao - e-commerce platform with CDN
#     "www.bilibili.com",        # Bilibili - video platform with complex CDN
#     "www.sina.com.cn",         # Sina - news portal with stable resolution
    
#     # 1.2 Educational institutions (typically simple A records)
#     "www.tsinghua.edu.cn",     # Tsinghua University - simple A record
#     "www.pku.edu.cn",          # Peking University - educational domain
#     "www.fudan.edu.cn",        # Fudan University - another educational domain
    
#     # 1.3 International domains for global resolution testing
#     "www.github.com",          # GitHub - international tech platform
#     "www.stackoverflow.com",   # Stack Overflow - developer community
#     "www.wikipedia.org",       # Wikipedia - global knowledge base
    
#     # ==============================================================================
#     # --- Category 2: DNS Redirection Test Cases (from redirect_map) ---
#     # ==============================================================================
    
#     # 2.1 Google services redirection (redirected to 127.0.0.1)
#     "www.google.com",          # Main Google search - should redirect to 127.0.0.1
#     "google.com",              # Google root domain - should redirect to 127.0.0.1
    
#     # 2.2 Ad tracking services redirection (redirected to 0.0.0.0)
#     "www.google-analytics.com", # Google Analytics - should redirect to 0.0.0.0
#     "doubleclick.net",         # DoubleClick ads - should redirect to 0.0.0.0
    
#     # 2.3 Friendly redirection test
#     "friendly.name",           # Custom friendly domain - should redirect to 8.8.8.8
    
#     # ==============================================================================
#     # --- Category 3: DNS Filtering Test Cases (from blocklist) ---
#     # ==============================================================================
    
#     # 3.1 Malware and phishing domains (blocked)
#     "malware-site.com",        # Malware domain - should be blocked
#     "phishing-attack.net",     # Phishing domain - should be blocked
    
#     # 3.2 Ad and tracking domains (blocked)
#     "ads.annoying-tracker.com", # Ad tracker - should be blocked
#     "stats.unwanted-data-miner.org", # Data mining tracker - should be blocked
    
#     # 3.3 Distracting content domains (blocked)
#     "distracting-social-media.com", # Social media distraction - should be blocked
    
#     # ==============================================================================
#     # --- Category 4: Edge Cases and Error Testing ---
#     # ==============================================================================
    
#     # 4.1 Non-existent domains (should return NXDOMAIN)
#     "nonexistent-domain-12345.com", # Non-existent domain
#     "this-domain-does-not-exist.net", # Another non-existent domain
    
#     # 4.2 Subdomain testing (not in redirect rules)
#     "mail.google.com",         # Google mail subdomain (not in redirect rules)
#     "drive.google.com",        # Google Drive subdomain (not in redirect rules)
#     "maps.google.com",         # Google Maps subdomain (not in redirect rules)
    
# ]

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5533


def run_dig(domain, thread_id, results_list):
    """
    Execute the 'dig' command. This function has two purposes:
    1. Immediately print the full dig response for real-time observation.
    2. Parse the response and store structured results in a shared list for final statistics.
    """
    command = f"dig @{SERVER_IP} {domain} a -p {SERVER_PORT}"
    print(f"[Thread-{thread_id:02d}] Executing: {command}")

    start_time = time.time()
    result_dict = {
        "domain": domain,
        "status": "UNKNOWN",
        "details": "",
        "duration": 0.0
    }

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        end_time = time.time()
        duration = end_time - start_time
        result_dict["duration"] = duration

        # ==========================================================
        # 1. Real-time intermediate output (print raw result immediately)
        # ==========================================================
        print(f"--- [Thread-{thread_id:02d}] Result for {domain} (took {duration:.2f}s) ---")
        print(result.stdout.strip())
        if result.stderr:
            print("--- Stderr ---")
            print(result.stderr.strip())
        print("-" * 50)

        # ==========================================================
        # 2. Data collection (parse result for final statistics)
        # ==========================================================
        stdout = result.stdout
        if "ANSWER SECTION" in stdout and "status: NOERROR" in stdout:
            result_dict["status"] = "SUCCESS"
            # answer_lines = [line for line in stdout.splitlines() if "\tA\t" in line or "\tCNAME\t" in line]
            answer_lines = [line for line in stdout.splitlines() 
                            if "A" in line.replace("\t", " ") or "CNAME" in line.replace("\t", " ")]
            if answer_lines:
                result_dict["details"] = f"-> {answer_lines[-1].split()[-1]}"
            else:
                result_dict["details"] = "-> (No A/CNAME in Answer)"
        elif "status: NXDOMAIN" in stdout:
            result_dict["status"] = "NXDOMAIN"
            result_dict["details"] = "-> Domain Not Found"
        else:
            result_dict["status"] = "ERROR"
            status_line = [line for line in stdout.splitlines() if "status:" in line]
            if status_line:
                result_dict["details"] = f"-> {status_line[0].split('status: ')[1].split(',')[0]}"
            else:
                result_dict["details"] = "-> Unexpected Response"

    except subprocess.TimeoutExpired:
        duration = 10.0
        result_dict["duration"] = duration
        result_dict["status"] = "TIMEOUT"
        result_dict["details"] = "-> Query timed out!"

        # Real-time output for timeout
        print(f"--- [Thread-{thread_id:02d}] Query for {domain} timed out! ---")

    # Append this thread's structured result to the shared list
    results_list.append(result_dict)


def main(domain_names, parallel_test=True):
    threads = []
    all_results = []

    print(f"Starting 20 concurrent DNS queries to {SERVER_IP}:{SERVER_PORT}...")
    start_total_time = time.time()

    for i, domain in enumerate(domain_names):
        thread = threading.Thread(target=run_dig, args=(domain, i, all_results))
        threads.append(thread)
        thread.start()
        if not parallel_test:
            thread.join()

    if parallel_test:
        for thread in threads:
            thread.join()

    end_total_time = time.time()

    # ==============================================================================
    # --- Final Summary Output ---
    # After all real-time outputs are complete, generate a clear categorized summary.
    # ==============================================================================
    print("\n" + "=" * 60)
    print(f"All {len(all_results)} queries completed in {end_total_time - start_total_time:.2f} seconds.")
    print("=" * 60)

    categorized_results = defaultdict(list)
    for res in all_results:
        categorized_results[res["status"]].append(res)

    print("\n📊 DNS Query Test Summary:\n")

    success_list = categorized_results.get("SUCCESS", [])
    print(f"✅ SUCCESS ({len(success_list)} queries):")
    if success_list:
        for res in sorted(success_list, key=lambda x: x["duration"]):
            print(f"   ({res['duration']:4.2f}s) - {res['domain']:<25} {res['details']}")
    else:
        print("   None")

    nxdomain_list = categorized_results.get("NXDOMAIN", [])
    print(f"\n⚠️ NXDOMAIN ({len(nxdomain_list)} queries):")
    if nxdomain_list:
        for res in sorted(nxdomain_list, key=lambda x: x["duration"]):
            print(f"   ({res['duration']:4.2f}s) - {res['domain']:<25} {res['details']}")
    else:
        print("   None")

    timeout_list = categorized_results.get("TIMEOUT", [])
    print(f"\n❌ TIMEOUT ({len(timeout_list)} queries):")
    if timeout_list:
        for res in sorted(timeout_list, key=lambda x: x["domain"]):
            print(f"   ({res['duration']:4.2f}s) - {res['domain']:<25} {res['details']}")
    else:
        print("   None")

    error_list = categorized_results.get("ERROR", [])
    print(f"\n❓ OTHER ERRORS ({len(error_list)} queries):")
    if error_list:
        for res in sorted(error_list, key=lambda x: x["duration"]):
            print(f"   ({res['duration']:4.2f}s) - {res['domain']:<25} {res['details']}")
    else:
        print("   None")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main(DOMAINS_TO_TEST)