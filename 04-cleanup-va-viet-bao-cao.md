# 04 - Cleanup và viết báo cáo

## 1. Cleanup sau lab

Chỉ cleanup sau khi đã chụp screenshot và export log cần thiết.

### 1.1. Xóa file tải về trên victim

Trên victim, mở PowerShell:

```powershell
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "FilelessLabDemo" -ErrorAction SilentlyContinue
Remove-Item -Path "$env:TEMP\FilelessLab" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:USERPROFILE\Downloads\ThongBaoLuong_Q3.zip" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:USERPROFILE\Downloads\ThongBaoLuong_Q3" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$env:USERPROFILE\Downloads\ThongBaoLuong_Q3.lnk" -Force -ErrorAction SilentlyContinue
```

Nếu bạn giải nén ZIP ra Desktop hoặc thư mục khác, xóa thêm thư mục đó.

### 1.2. Dừng các server trên attacker

Ở hai cửa sổ đang chạy:

```text
python -m http.server 8000 --bind 192.168.141.1
python .\collect_server.py
```

Nhấn:

```text
Ctrl + C
```

### 1.3. Xóa thư mục lab trên attacker nếu muốn

Trên attacker:

```powershell
Remove-Item -Path C:\Fileless-Lab -Recurse -Force
```

Chỉ chạy lệnh này sau khi đã lưu lại screenshot, ZIP, LNK hoặc log cần dùng cho báo cáo.

### 1.4. Khôi phục bằng snapshot

Cách sạch nhất với victim:

- Tắt VM.
- Revert về snapshot trước lab.

## 2. Export log để đưa vào báo cáo

### 2.1. Export Sysmon log

Trong Event Viewer:

```text
Applications and Services Logs
  Microsoft
    Windows
      Sysmon
        Operational
```

Click:

```text
Save All Events As...
```

Gợi ý lưu:

```text
C:\Users\<user>\Desktop\sysmon-operational.evtx
```

### 2.2. Export PowerShell log

Trong Event Viewer:

```text
Applications and Services Logs
  Microsoft
    Windows
      PowerShell
        Operational
```

Filter:

```text
4104
```

Sau đó lưu các event liên quan.

### 2.3. Export Security log nếu có

Trong Event Viewer:

```text
Windows Logs
  Security
```

Filter Event ID:

```text
4688
```

Lưu các event liên quan đến `powershell.exe`.

## 3. Ảnh cần đưa vào báo cáo

Nên có tối thiểu:

- Ảnh mô hình 2 máy hoặc bảng IP attacker/victim.
- Ảnh thư mục `C:\Fileless-Lab` trên attacker có `payload.ps1`, `ThongBaoLuong_Q3.lnk`, `ThongBaoLuong_Q3.zip`.
- Ảnh static server port `8000` đang host ZIP/payload.
- Ảnh collector server port `8001` đang nhận `/collect`.
- Ảnh victim truy cập `http://192.168.141.1:8000/`.
- Ảnh victim tải `ThongBaoLuong_Q3.zip`.
- Ảnh victim giải nén và thấy `ThongBaoLuong_Q3.lnk`.
- Ảnh victim không thấy popup/success rõ ràng sau khi mở LNK.
- Ảnh static server có request `GET /ThongBaoLuong_Q3.zip`.
- Ảnh static server có request `GET /payload.ps1`.
- Ảnh collector server có request `POST /collect`.
- Ảnh file `collections\victim-profile-*.json` trên attacker.
- Ảnh kịch bản mất mạng: file `%TEMP%\FilelessLab\queue\victim-profile-*.json` trên victim.
- Ảnh kịch bản có mạng lại: queued profile được gửi sang attacker.
- Ảnh Registry Run key `FilelessLabDemo` trên victim.
- Ảnh Sysmon Event ID 1 cho `powershell.exe`.
- Ảnh Sysmon Event ID 3 cho kết nối đến `192.168.141.1:8000`.
- Ảnh Sysmon Event ID 3 cho kết nối đến `192.168.141.1:8001` khi collector online.
- Ảnh PowerShell Event ID 4104.
- Ảnh kiểm tra không có `payload.ps1`, `payload.exe`, `payload.dll`, `payload.b64`, `payload-decoded.ps1` trên victim.

Không cần chụp:

- `certutil -decode`.
- `payload.b64`.
- `payload-decoded.ps1`.
- Persistence nguy hiểm hoặc ẩn mình.
- Calculator.

Các mục đó thuộc bản lab cũ.

## 4. Cách viết Chương 3

### 4.1. Mục tiêu lab

Có thể viết:

> Mục tiêu của bài lab là mô phỏng an toàn một chuỗi Astaroth-inspired Fileless Malware trên hai máy. Máy attacker host trang HR giả, file ZIP mồi nhử và payload vô hại, trong khi máy victim tải ZIP, giải nén shortcut LNK và mở shortcut. Shortcut gọi PowerShell để tải nội dung `payload.ps1` từ attacker qua HTTP port `8000`, tạo ScriptBlock trong bộ nhớ và thực thi trực tiếp. Payload sau đó thu thập thông tin máy không nhạy cảm, gửi JSON profile về attacker qua `POST /collect` trên port `8001`. Nếu kênh collector bị mất nhưng payload server vẫn truy cập được, profile được lưu tạm vào `%TEMP%\FilelessLab\queue` để mô phỏng offline staging; khi collector hoạt động lại, payload gửi queue về attacker. Lab cũng tạo Registry Run key vô hại để mô phỏng persistence và retry.

### 4.2. Môi trường lab

Lập bảng:

```text
Thành phần              Mô tả
Attacker                Windows thật, IP 192.168.141.1
Victim                  Windows VM, IP 192.168.141.140
Python static server    Host ZIP và payload.ps1 trên port 8000
Python collector server Nhận POST /collect trên port 8001
Sysmon                  Ghi log process, network, file create
PowerShell Logging      Ghi script block Event ID 4104
Event Viewer            Đọc và export log
```

### 4.3. Kịch bản mô phỏng

Viết theo từng bước:

1. Tạo payload vô hại `payload.ps1` trên attacker.
2. Tạo shortcut `ThongBaoLuong_Q3.lnk` gọi PowerShell.
3. Nén shortcut thành `ThongBaoLuong_Q3.zip`.
4. Attacker host ZIP/payload bằng Python static server port `8000` và chạy collector port `8001`.
5. Victim tải ZIP từ `http://192.168.141.1:8000/`.
6. Victim giải nén ZIP và mở shortcut.
7. PowerShell trên victim tải nội dung `payload.ps1` qua HTTP.
8. Nội dung payload được tạo thành ScriptBlock và thực thi trong memory.
9. Payload thu thập thông tin máy không nhạy cảm.
10. Payload gửi JSON profile về attacker.
11. Nếu không có mạng, payload lưu profile vào `%TEMP%\FilelessLab\queue`.
12. Khi mạng quay lại, payload gửi queue về attacker.
13. Payload tạo Registry Run key `FilelessLabDemo` để mô phỏng persistence và retry.
14. Thu thập log Sysmon, PowerShell 4104, Security 4688 và Registry event nếu Sysmon config có bật.

### 4.4. Phân tích kết quả

Có thể viết:

> Kết quả lab cho thấy một payload có thể được tải qua mạng và thực thi bởi PowerShell mà không cần lưu thành file payload rõ ràng trên ổ đĩa của victim. Trên attacker, static server port `8000` ghi nhận request tải `ThongBaoLuong_Q3.zip` và `payload.ps1`, còn collector server port `8001` ghi nhận request `POST /collect` chứa JSON profile của victim. Khi collector bị tắt, victim xuất hiện file staging tại `%TEMP%\FilelessLab\queue\victim-profile-*.json`; khi collector hoạt động lại, queued profile được gửi về attacker. Trên victim, Sysmon Event ID 1 ghi nhận `powershell.exe` được sinh ra sau khi người dùng mở shortcut, Sysmon Event ID 3 ghi nhận kết nối từ PowerShell đến `192.168.141.1:8000` và `192.168.141.1:8001`, PowerShell Event ID 4104 ghi nhận nội dung script được xử lý, Registry Run key `FilelessLabDemo` thể hiện persistence mô phỏng, trong khi kiểm tra file system không thấy `payload.ps1`, `payload.exe`, `payload.dll`, `payload.b64` hoặc `payload-decoded.ps1`.

### 4.5. Giới hạn của lab

Cần nói rõ:

- Lab không dùng sample Astaroth thật.
- Không mô phỏng credential theft.
- Không mô phỏng C2 thật.
- Không mô phỏng ADS, ExtExport, DLL injection hoặc process injection.
- Chỉ mô phỏng persistence bằng Registry Run key vô hại, dễ phát hiện và dễ cleanup.
- Không có obfuscation hoặc AV bypass.
- Payload không hiển thị kết quả cho victim; bằng chứng thành công nằm ở log attacker và log phòng thủ.
- ZIP và LNK vẫn tồn tại trên victim; phần fileless nằm ở payload execution.

### 4.6. Kết luận Chương 3

Có thể viết:

> Thông qua lab, có thể thấy việc phát hiện Fileless Malware phụ thuộc nhiều vào khả năng quan sát hành vi và tương quan sự kiện. Dù payload không được lưu thành file trên victim, các dấu vết như `explorer.exe -> powershell.exe`, kết nối từ PowerShell đến máy attacker, nội dung script trong PowerShell Event ID 4104 và sự vắng mặt của file payload trên disk vẫn giúp người phòng thủ dựng lại chuỗi hành vi. Lab vì vậy minh họa rõ rằng fileless không có nghĩa là không để lại dấu vết, mà đòi hỏi cách phát hiện dựa trên hành vi thay vì chỉ dựa trên file.

## 5. Checklist hoàn thành lab

- [ ] Đã tạo `payload.ps1` vô hại trên attacker.
- [ ] Đã tạo `ThongBaoLuong_Q3.lnk`.
- [ ] Đã nén `ThongBaoLuong_Q3.lnk` thành `ThongBaoLuong_Q3.zip`.
- [ ] Đã host `C:\Fileless-Lab` bằng Python static server port `8000`.
- [ ] Đã chạy Python collector server port `8001`.
- [ ] Victim tải được `ThongBaoLuong_Q3.zip`.
- [ ] Victim giải nén và mở được `ThongBaoLuong_Q3.lnk`.
- [ ] Victim không thấy popup/success rõ ràng sau khi mở LNK.
- [ ] Static server port `8000` ghi nhận `GET /ThongBaoLuong_Q3.zip`.
- [ ] Static server port `8000` ghi nhận `GET /payload.ps1`.
- [ ] Collector server port `8001` ghi nhận `POST /collect`.
- [ ] Attacker nhận được `collections\victim-profile-*.json`.
- [ ] Khi mất mạng, victim có `%TEMP%\FilelessLab\queue\victim-profile-*.json`.
- [ ] Khi có mạng lại, queued profile được gửi sang attacker.
- [ ] Victim có Registry Run key `FilelessLabDemo`.
- [ ] Đã tìm được Sysmon Event ID 1 cho `powershell.exe`.
- [ ] Đã tìm được Sysmon Event ID 3 cho kết nối đến `192.168.141.1:8000`.
- [ ] Đã tìm được Sysmon Event ID 3 cho kết nối đến `192.168.141.1:8001` khi collector online.
- [ ] Đã tìm được PowerShell Event ID 4104.
- [ ] Đã kiểm tra không có payload file trên victim.
- [ ] Đã chụp screenshot kết quả.
- [ ] Đã viết phần giới hạn an toàn của lab.
- [ ] Đã cleanup Registry Run key `FilelessLabDemo`.
- [ ] Đã cleanup `%TEMP%\FilelessLab`.
