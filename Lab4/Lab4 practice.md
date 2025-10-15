# Lab4

## Practice 4.2

![image-20251015113713364](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251015113713364.png)

![image-20251015114245866](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251015114245866.png)

| Connection Type       | Src IP    | Dst IP    | Src port number | Dst port number | Status code |
| --------------------- | --------- | --------- | --------------- | --------------- | ----------- |
| Request in Example 2  | 127.0.0.1 | 127.0.0.1 | 49250           | 8080            | ----        |
| Response in Example 2 | 127.0.0.1 | 127.0.0.1 | 8080            | 49250           | 200 OK      |
| Request in Example 3  | 127.0.0.1 | 127.0.0.1 | 50279           | 5555            | ----        |
| Response in Example 3 | 127.0.0.1 | 127.0.0.1 | 5555            | 50279           | N/A (Echo)  |

## Practice 4.3

### 3-1

127.0.0.1:8000;10.32.199.61:8000 都可以

### 3-2

对127.0.0.1:8000和10.32.199.61:8000，都可以用lo0

![image-20251015120528327](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251015120528327.png)

![image-20251015120647215](/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251015120647215.png)

### 3-3

http://127.0.0.1:8000/不行

http://10.32.199.61:8000/可以

### 3-4

选WiFi：en0