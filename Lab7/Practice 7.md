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

## Practice 7.3

### (1)

### (2)

### (3)

### (4)

### (5)



