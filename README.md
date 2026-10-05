# Namespace Lab Fileless Malware

Đây là namespace tài liệu cho đề tài **Fileless Malware**. Mục tiêu là giúp người mới đi từ khái niệm cơ bản đến một demo lab an toàn theo hướng **Astaroth-inspired Living-off-the-Land**.

Lưu ý quan trọng: lab trong namespace này là bản mô phỏng an toàn, rút gọn để học log và detection. Nó không tái hiện đầy đủ chuỗi Astaroth thật được Microsoft mô tả.

## Bản lab hiện tại

Bản lab hiện tại dùng mô hình hai máy:

- Attacker: Windows thật, IP `192.168.141.1`.
- Victim: Windows VM, IP `192.168.141.140`.

Luồng chính:

```text
Victim tải ThongBaoLuong_Q3.zip
  -> giải nén ThongBaoLuong_Q3.lnk
  -> double click LNK
  -> LNK gọi powershell.exe
  -> PowerShell tải payload.ps1 từ attacker qua HTTP
  -> nội dung payload được giữ trong RAM
  -> PowerShell tạo ScriptBlock và thực thi
  -> payload thu thập profile máy không nhạy cảm
  -> payload gửi JSON về attacker qua POST /collect trên port 8001
  -> nếu collector 8001 không chạy, payload lưu profile vào %TEMP%\FilelessLab\queue
  -> khi có mạng lại, payload gửi queue về attacker
  -> payload tạo Registry Run key vô hại để mô phỏng persistence
```

Điểm quan trọng:

- Không dùng mã độc thật.
- Không dùng `payload.b64`.
- Không dùng `certutil -decode`.
- Không tạo `payload-decoded.ps1` trên victim.
- Payload thu thập thông tin máy không nhạy cảm như hostname, username, OS version và IP nội bộ.
- Payload không lấy password, cookie, token, clipboard, browser data hoặc tài liệu cá nhân.
- Offline staging chỉ lưu profile không nhạy cảm tại `%TEMP%\FilelessLab\queue`.
- Persistence chỉ là Registry Run key vô hại để mô phỏng retry, có cleanup rõ ràng.
- ZIP và LNK vẫn tồn tại trên victim, nhưng payload không được lưu thành file trên victim.
- Victim không thấy popup/success rõ ràng; người làm lab xác nhận thành công bằng log `POST /collect` trên collector port `8001` và file `collections\victim-profile-*.json` trên attacker.

## Cách đọc nhanh

1. Đọc `01-chuan-bi-moi-truong.md` để chuẩn bị VM, Sysmon, PowerShell logging, `gpedit.msc` và network.
2. Đọc `02-lab-2-may-astaroth-style.md` để tạo payload, tạo LNK, zip LNK và chạy lab hai máy.
3. Đọc `03-detection-phong-thu.md` để hiểu cách đọc Sysmon, PowerShell 4104 và logic phát hiện.
4. Đọc `04-cleanup-va-viet-bao-cao.md` để dọn lab, export log và viết phần kết quả.

## Nguyên tắc an toàn

- Không dùng sample mã độc thật.
- Không tải payload từ Internet không tin cậy.
- Không chạy victim trực tiếp trên máy chính.
- Chỉ dùng payload vô hại.
- Không hướng dẫn bypass antivirus.
- Chỉ mô phỏng hành vi để học cách phát hiện qua log.

## Các file trong namespace

- `README.md`: trang chỉ mục.
- `01-chuan-bi-moi-truong.md`: chuẩn bị VM, Sysmon, logging và `gpedit.msc`.
- `02-lab-2-may-astaroth-style.md`: lab 2 máy, attacker host ZIP/payload và victim mở LNK.
- `03-detection-phong-thu.md`: cách đọc log, detection logic, Sigma mẫu và phòng thủ.
- `04-cleanup-va-viet-bao-cao.md`: cleanup lab và gợi ý viết Chương 3.
- `lab-files/attacker-web`: bộ file mẫu để copy sang `C:\Fileless-Lab`.

## Ghi chú về file cũ

Một số file cũ như `02-lab-astaroth-style.md` hoặc tài liệu nháp trước đây có thể vẫn nhắc đến `wmic`, `payload.b64`, `certutil` hoặc `payload-decoded.ps1`. Bản nên follow hiện tại là:

```text
01-chuan-bi-moi-truong.md
02-lab-2-may-astaroth-style.md
03-detection-phong-thu.md
04-cleanup-va-viet-bao-cao.md
```
