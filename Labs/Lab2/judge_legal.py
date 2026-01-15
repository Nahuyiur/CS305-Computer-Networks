def parse_ipv4(str):
    parts=str.split(".")
    if len(parts)!=4:
        return None
    try:
        nums=[int(x) for x in parts]
    except ValueError:
        return None
    
    for x in nums:
        if x<0 or x >255:
            return None
    
    return nums

def judge_valid_mask(mask_nums):
    if mask_nums is None or len(mask_nums) != 4:
        return False
    
    allowed={0,128,192,224,240,248,252,254,255}
    for num in mask_nums:
        if num not in allowed:
            return False
        
    seen_non255 = False
    seen_non255 = False
    for i, b in enumerate(mask_nums):
        if not seen_non255:
            if b == 255:
                continue
            seen_non255 = True
            if any(x != 0 for x in mask_nums[i+1:]):
                return False
        else:
            if b != 0:
                return False
            
    if mask_nums==[0,0,0,0]:
        return False
    return True


def to_int(nums):
    v = 0
    for n in nums:
        v = (v << 8) | n
    return v

def to_dotted(n):
    return ".".join(str((n >> shift) & 0xFF) for shift in (24,16,8,0))

def handle(ip_str, mask_str):
    ip = parse_ipv4(ip_str)
    if ip is None:
        return "IP address illegal"
    mask = parse_ipv4(mask_str)
    if not judge_valid_mask(mask):
        return "subnet mask illegal"

    ip_i = to_int(ip)
    mask_i = to_int(mask)
    net_i = ip_i & mask_i
    host_i = ip_i & (~mask_i & 0xFFFFFFFF)

    return f"network ID: {to_dotted(net_i)}, host ID: {host_i & 0xFF}"

print(handle("192.168.1.155", "255.255.255.0"))
print(handle("192.168.1.355", "255.255.255.0"))
print(handle("192.168.1.155", "255.253.255.0"))