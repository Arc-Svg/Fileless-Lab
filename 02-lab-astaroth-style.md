# 02 - Lab mô phỏng Astaroth-style Fileless Malware

## 1. Ý tưởng lab

Trong thực tế, Astaroth-style attack thường lạm dụng công cụ hợp pháp của Windows, còn gọi là **Living-off-the-Land**.

Trong lab này, ta mô phỏng chuỗi sau:

```text
Người dùng chạy script giả lập
        |
        v
wmic tạo process PowerShell
        |
        v
PowerShell/BITS tải payload vô hại từ local HTTP server
        |
        v
certutil decode payload vô hại
        |
        v
PowerShell chạy payload vô hại
        |
        v
Payload tạo file kết quả
```

Payload vô hại chỉ tạo file text. Không có mã độc, không đánh cắp dữ liệu, không kết nối C2.

## 2. Chuẩn bị payload vô hại

Mở PowerShell trong VM.

Tạo file payload vô hại:

```powershell
Set-Content -Path C:\Lab\Fileless\server\payload.ps1 -Value @'
$out = "C:\Lab\Fileless\work\lab-result.txt"
$time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"Astaroth-style benign payload executed at $time" | Out-File -FilePath $out -Encoding utf8
Add-Type -AssemblyName PresentationFramework
[void][System.Windows.MessageBox]::Show(
    "Máy bị hack! Đây là popup giả lập cho lab Fileless Malware. Không có mã độc thật được chạy.",
    "Astaroth-style Lab Demo",
    "OK",
    "Warning"
)
'@
```

Payload này làm 2 việc vô hại:

- Ghi timestamp vào `C:\Lab\Fileless\work\lab-result.txt`.
- Hiện popup cảnh báo giả lập để dễ nhìn thấy payload đã chạy thành công.

## 3. Mã hóa payload thành Base64

`certutil` sẽ được dùng để decode file Base64. Để có file Base64, chạy:

```powershell
certutil -encode C:\Lab\Fileless\server\payload.ps1 C:\Lab\Fileless\server\payload.b64
```

Kiểm tra file:

```powershell
Get-ChildItem C:\Lab\Fileless\server
```

Bạn nên thấy:

```text
payload.ps1
payload.b64
```

## 4. Mở local HTTP server

Trong PowerShell, chạy:

```powershell
cd C:\Lab\Fileless\server
python -m http.server 8000
```

Nếu máy không có Python, có thể bỏ qua phần download và copy file trực tiếp. Tuy nhiên có local HTTP server sẽ giúp log đẹp hơn vì có hành vi download.

Kiểm tra bằng trình duyệt trong VM:

```text
http://127.0.0.1:8000/payload.b64
```

Nếu trình duyệt hiện nội dung Base64 là được.

## 5. Mở terminal thứ hai để chạy attack simulation

Mở một PowerShell khác bằng quyền user bình thường hoặc Administrator đều được.

### Bước 1: Dùng wmic gọi PowerShell

Lệnh này mô phỏng việc `wmic.exe` tạo process PowerShell. Trong attack thật, đây là dấu hiệu đáng chú ý vì công cụ quản trị Windows lại gọi script engine.

h 
```

Kiểm tra:

```powershell
Get-Content C:\Lab\Fileless\work\wmic-step.txt
```

Điều cần quan sát trong log:

- Parent process: `wmic.exe`.
- Child process: `powershell.exe`.
- Command line có `-ExecutionPolicy Bypass`.

### Bước 2: Dùng BITS để tải payload Base64

BITS là cơ chế hợp pháp của Windows để truyền file nền. Malware có thể lạm dụng nó để tải payload.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-BitsTransfer -Source http://127.0.0.1:8000/payload.b64 -Destination C:\Lab\Fileless\work\payload.b64"
```

Kiểm tra:

```powershell
Get-ChildItem C:\Lab\Fileless\work
```

Bạn nên thấy file:

```text
payload.b64
```

Điều cần quan sát trong log:

- PowerShell command có `Start-BitsTransfer`.
- Có network connection đến `127.0.0.1:8000`.
- Có file create `payload.b64`.

### Bước 3: Dùng certutil decode payload

`certutil` là công cụ hợp pháp của Windows, nhưng hay bị lạm dụng để encode/decode hoặc tải file.

```powershell
certutil -decode C:\Lab\Fileless\work\payload.b64 C:\Lab\Fileless\work\payload-decoded.ps1
```

Kiểm tra:

```powershell
Get-Content C:\Lab\Fileless\work\payload-decoded.ps1
```

Điều cần quan sát trong log:

- Process `certutil.exe`.
- Command line có `-decode`.
- File output `payload-decoded.ps1`.

### Bước 4: Chạy payload vô hại

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Lab\Fileless\work\payload-decoded.ps1
```

Kiểm tra kết quả:

```powershell
Get-Content C:\Lab\Fileless\work\lab-result.txt
```

Bạn cũng sẽ thấy một popup cảnh báo giả lập xuất hiện.

Điều cần quan sát trong log:

- `powershell.exe` chạy file script.
- Script tạo `lab-result.txt`.
- PowerShell load `PresentationFramework` để hiển thị popup.

## 6. Optional: Mô phỏng Registry persistence vô hại

Phần này chỉ để minh họa persistence. Không bắt buộc.

Persistence nghĩa là tạo cơ chế để chương trình tự chạy lại sau khi user login hoặc máy reboot.

Tạo Run key vô hại:

```powershell
New-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "FilelessLabBenign" -Value "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Lab\Fileless\work\payload-decoded.ps1" -PropertyType String -Force
```

Kiểm tra:

```powershell
Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" | Select-Object FilelessLabBenign
```

Cần lưu ý:

- Đây là minh họa cơ chế persistence.
- Nên cleanup ngay sau lab.
- Không nên để Run key này tồn tại trên máy thật.

## 7. Nơi cần chụp screenshot

Chụp các màn hình sau để đưa vào báo cáo:

- Thư mục `C:\Lab\Fileless\server` có `payload.ps1` và `payload.b64`.
- Local HTTP server đang chạy.
- Lệnh `wmic` gọi PowerShell.
- File `wmic-step.txt` được tạo.
- File `payload.b64` được download.
- Lệnh `certutil -decode`.
- File `lab-result.txt`.
- Popup cảnh báo giả lập xuất hiện.
- Sysmon Event ID 1 liên quan `wmic.exe`, `powershell.exe`, `certutil.exe`.
- PowerShell Event ID 4104.

## 8. Bạn vừa mô phỏng điều gì?

Bạn vừa mô phỏng các ý chính của Astaroth-style:

- Dùng công cụ hợp pháp của Windows thay vì file malware rõ ràng.
- Dùng `wmic` để tạo process.
- Dùng PowerShell/BITS để tải payload.
- Dùng `certutil` để xử lý/mã hóa/giải mã nội dung.
- Dùng log để phát hiện hành vi đáng ngờ.

Khác với mã độc thật:

- Payload của bạn vô hại.
- Download chỉ từ local HTTP server.
- Không có C2.
- Không có credential theft.
- Không có persistence ẩn sâu nếu bạn cleanup đúng cách.
