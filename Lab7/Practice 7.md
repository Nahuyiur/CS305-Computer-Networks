# Practice 7

## Practice 7.1 

### (1)

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251103155404981.png" alt="image-20251103155404981" style="zoom:50%;" />

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251103155301256.png" alt="image-20251103155301256" style="zoom:50%;" />

UDP头部有4个fields：source port, destination port, length, checksum

### (2)

source port:63392, destination port: 63392, length: 40 bytes, checksum: 0x003b(unverified)

### (3)

UDP报文头结构长度固定，每个field都是2bytes

### (4)

length字段占16bits，最大的无符号数是:$2^{16}-1=65535$

最大的总长度（header+data）为65535bytes

### (5)

port字段同样是16bits，因此最大的端口号是65535

### (6)

协议id：17(decimal)/0x11(hex)

## Practice 7.2

### (1)

![image-20251105112130035](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251105112130035.png)

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251105112152063.png" alt="image-20251105112152063" style="zoom:50%;" />

source ip: 192.168.1.102, source port: 1161

### (2)

destination ip: 128.119.245.12, detination port: 80

### (4)

![image-20251105114721302](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251105114721302.png)

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251105114818712.png" alt="image-20251105114818712" style="zoom:50%;" />

sequence number(raw): 232129012; syn是1

### (5)

![image-20251105115133335](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251105115133335.png)

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251105115211803.png" alt="image-20251105115211803" style="zoom:50%;" />

sequence number(raw): 883061785； acknowledgement number(raw): 232129013

根据前一个的syn包中的sequence number + 1表示接下来希望收到的sequence number是多少

syn = 1，acknowledgement = 1

### (6)

![image-20251105115549243](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251105115549243.png)

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251105115611947.png" alt="image-20251105115611947" style="zoom:50%;" />

sequence number(raw): 232293053

### (11)

![image-20251105115925139](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251105115925139.png)

通常ACK确认 1460bytes数据

![image-20251105120209594](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251105120209594.png)

但是这里ack = 37969下一条ack = 40889，是隔一段确认的（延迟确认）

### (12)

![image-20251105120616203](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251105120616203.png)

对第一个tcp包跟踪流，可以看到整个对话的字节数164kB

起始时间0.023172s，终止时间5.651141s

$\text{throughtput}=164 \times 1024/ (5.651141 - 0.026477)=29857.07 \text{Bytes/s}$



