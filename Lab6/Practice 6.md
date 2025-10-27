# Practice 6

## Practice 6.1

```bash
curl -I http://www.sina.com.cn
```

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251027155431728.png" alt="image-20251027155431728" style="zoom:50%;" />

X-Via-CDN字段表明使用CDN

```bash
nslookup www.sina.com.cn
```

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251027155700610.png" alt="image-20251027155700610" style="zoom:50%;" />

CDN的地址如图所示

不同的地方可能得到不同的ip：124.239.198.145, 122.227.101.220

## Practice 6.2

![image-20251027175234745](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251027175234745.png)

开三个窗口，有3次http握手

![image-20251027175247039](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251027175247039.png)

![image-20251027180147509](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251027180147509.png)

客户端向服务器发送hello world

![image-20251027180413325](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251027180413325.png)

![image-20251027180248200](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251027180248200.png)

服务器确定接受客户端消息后（ACK），向其他客户端广播

---

