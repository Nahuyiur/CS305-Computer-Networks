# Practice 5

## Practice5.1

### （1）

dig +trace www.sina.com.cn 运行结果：

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251016225746084.png" alt="image-20251016225746084" style="zoom:50%;" />

### （2）

wireshark capture结果：

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251016225859520.png" alt="image-20251016225859520" style="zoom:50%;" />

### （3）

从local host一共有15个query，transaction id不一样

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251016230305660.png" alt="image-20251016230305660" style="zoom:50%;" />

### （4）

local host收到了15个response

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251016230418588.png" alt="image-20251016230418588" style="zoom:50%;" />

### （5）

RD是1（但是向根服务器的查询的RD是0）；local DNS server的response中，RA是1

这个是query：<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251016231336139.png" alt="image-20251016231336139" style="zoom:50%;" />

这个是response：

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251016231413145.png" alt="image-20251016231413145" style="zoom:50%;" />

### （6）<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251016231810458.png" alt="image-20251016231810458" style="zoom:50%;" />

发出最后一个response的是198.18.0.234，是Authoritative DNS server

Source (Src) = `198.18.0.234`，name=www.sina.com.cn，port number of the server=53；

有answers：Answer RRs：1；

AA=1

### （7）

重新做query

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251016232314194.png" alt="image-20251016232314194" style="zoom:50%;" />

source ip改变了，变成了**198.18.0.240**；其他没什么变的，返回内容也相同：www.sina.com.cn → 198.18.0.242

原因：DNS 解析通常使用轮询（Round Robin）或地理负载均衡；客户端或中间 DNS 服务器可能会从权威服务器列表中随机选择一个进行查询，以分散流量

好处：可靠，防止权威服务器单点宕机；提高性能，分担负载

