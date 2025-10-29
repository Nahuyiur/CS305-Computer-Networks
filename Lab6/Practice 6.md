# Practice 6

## Practice 6.1

```bash
curl -I http://www.sina.com.cn
```

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251027155431728.png" alt="image-20251027155431728" style="zoom:50%;" />

X-Via-CDN字段表明使用CDN



查询sina的ip用以下命令：

![image-20251029175537479](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251029175537479.png)

sina的ip如图所示



查询cdn用以下命令：

```bash
curl -v http://www.sina.com.cn 2>&1 grep "Connected to"
```

![image-20251029175130213](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251029175130213.png)

CDN的地址：240e:97c:38:600:3::3e8



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

