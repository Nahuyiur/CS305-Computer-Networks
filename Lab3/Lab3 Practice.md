# Lab3 Practice

## Practice 3.1

text/html

image/jpeg

video/mp4

application/javascript

image/svg+xml

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251011172102371.png" alt="image-20251011172102371" style="zoom:50%;" />

---

## Practice 3.2

| #    | URL                        | Status code | Meaning                    | Port number of server | Port number of client |
| ---- | -------------------------- | ----------- | -------------------------- | --------------------- | --------------------- |
| 1    | http://www.sustech.edu.cn  | 200         | OK                         | 80                    | 58866                 |
| 2    | https://www.sustech.edu.cn | 200         | OK                         | 443                   | 58867                 |
| 3    | http://sustech.edu.cn      | 301         | Moved Permanently          | 80                    | 53963                 |
| 4    | https://sustech.edu.cn     | 200         | OK                         | 443                   | 59556                 |
| 5    | http://sina.com.cn         | 301         | Moved Permanently          | 80                    | 59557                 |
| 6    | http://www.sina.com.cn     | 302         | Found (Temporary Redirect) | 80                    | 59558                 |
| 7    | https://www.sina.com.cn    | 200         | OK                         | 443                   | 59559                 |

status code的含义：

- 200 OK（成功）
- 301/308 Moved Permanently（永久重定向）
- 302/307 Found/Temporary Redirect（临时重定向）

问题（1）：

- 客户端端口：不相同，每次连接都使用不同的临时端口（58866, 59557, 59558,53963）
- 服务器端口：相同，都是80端口（HTTP标准端口）

问题（2）：

- 客户端端口：不相同，每次连接都使用不同的临时端口（58867, 59556, 59559）

- 服务器端口：相同，都是443端口（HTTPS标准端口）

<img src="/Users/ruiyuhan/Library/Application Support/typora-user-images/image-20251011175230385.png" alt="image-20251011175230385" style="zoom:50%;" />