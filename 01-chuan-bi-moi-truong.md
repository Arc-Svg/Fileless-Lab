# 01 - Chuẩn bị môi trường lab Astaroth-inspired

## 1. Mục tiêu của phần chuẩn bị

Bài lab này mô phỏng một chuỗi Fileless Malware theo hướng Astaroth-inspired trong môi trường an toàn. Mục tiêu không phải tạo mã độc thật, mà là giúp người học quan sát được cách một file shortcut `.lnk` có thể gọi PowerShell, tải nội dung payload từ máy attacker qua HTTP và thực thi nội dung đó trong bộ nhớ.

Lab chỉ dùng payload vô hại. Payload không đánh cắp dữ liệu, không tạo persistence, không kết nối C2 thật, không bypass antivirus và không leo thang đặc quyền.

Chuỗi tổng quan:

```text
Victim tải ZIP
  -> giải nén
  -> double click ThongBaoLuong_Q3.lnk
  -> LNK gọi powershell.exe
  -> PowerShell kết nối attacker qua HTTP
  -> nhận nội dung payload.ps1
  -> tạo ScriptBlock trong RAM
  -> thực thi payload
  -> hiển thị kết quả trong PowerShell
```

Điểm cần chứng minh:

- Có network connection từ victim đến attacker.
- Có PowerShell execution.
- Có nội dung payload được thực thi.
- Không có `payload.ps1`, `payload.exe`, `payload.dll`, `payload.b64` hoặc `payload-decoded.ps1` được ghi xuống ổ đĩa của victim.

## 2. Mô hình lab

Lab sử dụng hai máy trong mạng nội bộ cô lập:

| Vai trò | Máy | IP | Chức năng |
|---|---|---:|---|
| Attacker | Windows thật | `192.168.141.1` | Host `payload.ps1`, `ThongBaoLuong_Q3.zip` và nhận `POST /collect` bằng Python collector server |
| Victim | Windows VM | `192.168.141.140` | Truy cập web giả lập, tải ZIP, mở LNK và sinh log |

Yêu cầu chung:

- Hai máy ping được nhau.
- Victim truy cập được `http://192.168.141.1:8000/`.
- Attacker có Python 3.
- Victim có PowerShell, Event Viewer và Sysmon.
- Nên tạo snapshot cho máy ảo victim trước khi chạy lab.

## 3. Công cụ cần chuẩn bị

Bắt buộc:

- Windows Event Viewer.
- PowerShell.
- Sysmon.
- Python 3 trên máy attacker.
- Trình duyệt web trên máy victim.

Nên có thêm:

- Process Explorer.
- Process Monitor.
- Autoruns.

Tải Sysinternals từ Microsoft:

```text
https://learn.microsoft.com/sysinternals/
```

## 4. Cài Sysmon trên victim

### 4.1. Tải Sysmon

Tải Sysmon từ Microsoft Sysinternals và giải nén vào:

```text
C:\Tools\Sysmon
```

### 4.2. Tải Sysmon config

Có thể dùng config cộng đồng của SwiftOnSecurity:

```text
https://github.com/SwiftOnSecurity/sysmon-config
```

Lưu file config thành:

```text
C:\Tools\Sysmon\sysmonconfig.xml
```

### 4.3. Cài Sysmon

Mở PowerShell bằng quyền Administrator:

```powershell
cd C:\Tools\Sysmon
.\Sysmon64.exe -accepteula -i .\sysmonconfig.xml
```

Kiểm tra:

```powershell
Get-Service Sysmon*
```

Nếu cài đúng sẽ thấy service Sysmon đang chạy.

Log nằm tại:

```text
Event Viewer
  Applications and Services Logs
    Microsoft
      Windows
        Sysmon
          Operational
```

Event quan trọng trong lab:

- Sysmon Event ID 1: Process Creation.
- Sysmon Event ID 3: Network Connection.
- Sysmon Event ID 11: File Create.

## 5. Cài hoặc bật gpedit.msc nếu máy không có

Một số bản Windows Home không có sẵn Local Group Policy Editor. Nếu bấm `Win + R`, gõ `gpedit.msc` mà báo không tìm thấy, mở CMD bằng quyền Administrator và chạy lần lượt hai lệnh sau:

```cmd
FOR %i IN ("%SystemRoot%\servicing\Packages\Microsoft-Windows-GroupPolicy-ClientTools-Package~*.mum") DO (DISM /Online /NoRestart /Add-Package:"%i")
```

```cmd
FOR %i IN ("%SystemRoot%\servicing\Packages\Microsoft-Windows-GroupPolicy-ClientFolder-Package~*.mum") DO (DISM /Online /NoRestart /Add-Package:"%i")
```

Sau khi chạy xong, thử mở lại:

```text
Win + R
gpedit.msc
```

Nếu vẫn chưa mở được, restart máy ảo victim rồi kiểm tra lại.

## 6. Bật PowerShell Script Block Logging

Trên victim, mở:

```text
Win + R
gpedit.msc
```

Đi tới:

```text
Computer Configuration
  Administrative Templates
    Windows Components
      Windows PowerShell
```

Mở:

```text
Turn on PowerShell Script Block Logging
```

Chọn:

```text
Enabled
```

Cập nhật policy:

```powershell
gpupdate /force
```

Log cần xem:

```text
Event Viewer
  Applications and Services Logs
    Microsoft
      Windows
        PowerShell
          Operational
```

Event quan trọng:

- PowerShell Event ID 4104: nội dung script được PowerShell xử lý.

Nếu không dùng được `gpedit.msc`, có thể bật bằng PowerShell Administrator:

```powershell
New-Item -Path "HKLM:\Software\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -Force
Set-ItemProperty -Path "HKLM:\Software\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -Name EnableScriptBlockLogging -Value 1 -Type DWord
```

## 7. Bật Process Creation Audit

Mở PowerShell Administrator trên victim:

```powershell
auditpol /set /subcategory:"Process Creation" /success:enable
```

Kiểm tra:

```powershell
auditpol /get /subcategory:"Process Creation"
```

Log cần xem:

```text
Event Viewer
  Windows Logs
    Security
      Event ID 4688
```

Nếu muốn Security Event 4688 có cả command line, mở `gpedit.msc`:

```text
Computer Configuration
  Administrative Templates
    System
      Audit Process Creation
        Include command line in process creation events
```

Chọn:

```text
Enabled
```

Sau đó chạy:

```powershell
gpupdate /force
```

## 8. Bật hiển thị file extension trên victim

Vì bài lab có file ZIP và shortcut `.lnk`, cần bật hiển thị phần mở rộng file để dễ quan sát và chụp ảnh báo cáo.

Trên Windows 11:

```text
File Explorer
  View
    Show
      File name extensions
```

Trên Windows 10:

```text
File Explorer
  View
    File name extensions
```

## 9. Tạo thư mục lab trên attacker

Trên máy attacker `192.168.141.1`, mở PowerShell:

```powershell
mkdir C:\Fileless-Lab
cd C:\Fileless-Lab
```

Các file chính trong thư mục này:

```text
C:\Fileless-Lab
  payload.ps1
  create_lnk.ps1
  ThongBaoLuong_Q3.lnk
  ThongBaoLuong_Q3.zip
```

Ý nghĩa:

- `payload.ps1`: payload vô hại, thu thập profile máy không nhạy cảm, offline staging và mô phỏng persistence/retry.
- `collect_server.py`: web server kiêm collector nhận JSON profile từ victim.
- `create_lnk.ps1`: script tạo shortcut `.lnk`.
- `ThongBaoLuong_Q3.lnk`: launcher mà victim sẽ mở sau khi giải nén ZIP.
- `ThongBaoLuong_Q3.zip`: gói giả lập tài liệu mồi nhử để victim tải về.

## 10. Kiểm tra kết nối mạng

Trên victim:

```powershell
ipconfig
ping 192.168.141.1
```

Trên attacker:

```powershell
ipconfig
python --version
```

Nếu victim ping được attacker và attacker có Python, có thể chuyển sang file hướng dẫn thực hiện lab.

## 11. Checklist chuẩn bị

- [ ] Victim là Windows VM.
- [ ] Đã tạo snapshot cho victim.
- [ ] Attacker có IP `192.168.141.1`.
- [ ] Victim có IP `192.168.141.140`.
- [ ] Hai máy ping được nhau.
- [ ] Attacker có Python 3.
- [ ] Victim đã cài Sysmon.
- [ ] Victim đã bật PowerShell Script Block Logging.
- [ ] Victim đã bật Process Creation Audit.
- [ ] Nếu cần, victim đã cài/bật được `gpedit.msc`.
- [ ] Victim đã bật hiển thị file extension.
- [ ] Attacker đã có thư mục `C:\Fileless-Lab`.
