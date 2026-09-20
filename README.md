# RemoteSysWatch

> 5 Linux ve 5 Windows olmak üzere toplam 10 sistemi agent kullanmadan uzaktan izleyen, sorunları tespit edip inceleyen ve Telegram üzerinden bildiren Python tabanlı monitoring sistemi.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Linux](https://img.shields.io/badge/Linux-Ubuntu%20%2F%20AlmaLinux-orange)
![Windows](https://img.shields.io/badge/Windows-7%20%2F%2010%20%2F%2011-0078D6)
![Monitoring](https://img.shields.io/badge/Type-Agentless%20Monitoring-success)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen)

---

## Proje Hakkında

**RemoteSysWatch**, birden fazla Linux ve Windows sisteminin merkezi bir monitoring sunucusu üzerinden uzaktan izlenmesi amacıyla geliştirilmiş Python tabanlı bir sistem izleme projesidir.

İzlenen sistemlere herhangi bir monitoring agent kurulmaz. Merkezi monitoring sunucusu;

- Linux sistemlere **SSH / Paramiko**
- Windows sistemlere **WinRM**

üzerinden bağlanarak sistem bilgilerini toplar.

Toplanan veriler belirlenen eşiklerle karşılaştırılır. CPU, RAM, disk veya erişilebilirlik gibi konularda anormal bir durum tespit edildiğinde sistem yalnızca alarm üretmekle kalmaz; problem türüne göre hedef sistem üzerinde ek incelemeler gerçekleştirerek probleme ilişkin kullanılabilir bilgiler toplamaya çalışır.

Tespit edilen sorunlar Telegram üzerinden **ALERT**, sorun ortadan kalktığında ise **RECOVERY** bildirimi olarak gönderilir.

---

## Temel Mantık

RemoteSysWatch'in temel çalışma mantığı:

```text
                     ┌─────────────────────────┐
                     │    Monitoring Server     │
                     │         Python          │
                     └────────────┬────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                SSH / Paramiko              WinRM
                    │                           │
             ┌──────┴──────┐             ┌──────┴──────┐
             │             │             │             │
          Linux x5      Telemetry     Windows x5   Telemetry
             │             │             │             │
             └─────────────┴─────────────┴─────────────┘
                                  │
                                  ▼
                         Health Detection
                                  │
                                  ▼
                           Investigation
                                  │
                                  ▼
                             Diagnosis
                                  │
                                  ▼
                       Telegram Notification
                           │             │
                         ALERT        RECOVERY
```

Daha basit haliyle:

```text
Uzak cihazlara ulaş
        ↓
Bilgileri topla
        ↓
Sağlık durumunu analiz et
        ↓
Problem var mı?
      /   \
    Hayır  Evet
      │      │
      │  Investigation
      │      │
      │  Diagnosis
      │      │
      └──────┴──────→ Telegram
                         │
                       ALERT
                         │
                   Problem düzelir
                         │
                      RECOVERY
```

---

## Neden Bu Proje?

Bu proje; sistem izleme, Linux ve Windows yönetimi, uzaktan bağlantı, monitoring mantığı, troubleshooting ve otomasyon konularını tek bir sistem üzerinde bir araya getirmek amacıyla geliştirildi.

Gerçek kullanım senaryosunda bu tarz bir yapının daha çok sunucular, servisler ve altyapı sistemleri üzerinde kullanılması hedeflenmektedir.

Projede kullanılan Windows ve Linux makineler ise kişisel bilgisayarları izlemek için değil; farklı işletim sistemi sürümlerinden oluşan heterojen bir ortam oluşturmak, remote monitoring mekanizmalarını test etmek ve farklı platformlarda deneyim kazanmak amacıyla VMware üzerinde sanallaştırılmıştır.

---

## Öne Çıkan Özellikler

### Agentless Monitoring

İzlenen sistemlere ek bir monitoring agent kurulmaz.

Merkezi monitoring sunucusu doğrudan uzaktan bağlantı yöntemlerini kullanır:

- Linux → SSH / Paramiko
- Windows → WinRM

Böylece izleme işlemi merkezi bir sistem tarafından gerçekleştirilir.

### Çoklu İşletim Sistemi Desteği

Toplam 10 farklı sistem monitoring kapsamındadır.

**Linux**
- Ubuntu 18.04
- Ubuntu 22.04
- Ubuntu 24.04
- Ubuntu 26.04
- AlmaLinux 9

**Windows**
- Windows 7 Professional
- Windows 10 Pro
- Windows 10 Enterprise LTSC
- Windows 11 Pro
- Windows 11 Enterprise Evaluation

Bu çeşitlilik, sistemin tek bir işletim sistemine bağlı kalmadan farklı platformlarda test edilmesini sağlar.

### İzlenen Metrikler

RemoteSysWatch temel olarak aşağıdaki sistem bilgilerini toplar.

**CPU**
- CPU kullanım yüzdesi
- CPU çekirdek sayısı
- Linux load average
- Yüksek CPU kullanımında process incelemesi

**RAM**
- RAM kullanım yüzdesi
- Kullanılan RAM
- Toplam RAM
- Kullanılabilir RAM
- Yüksek RAM kullanımında process incelemesi
- Linux swap durumu
- Windows pagefile durumu

**Disk**
- Disk kullanım yüzdesi
- Kullanılan alan
- Toplam alan
- Boş alan
- Problem durumunda ilgili disk / mount incelemesi

**Sistem Bilgileri**
- İşletim sistemi
- İşletim sistemi sürümü
- Hostname
- IP adresi
- Uptime
- Network interface bilgileri

### Health Detection

Toplanan sistem verileri merkezi threshold değerleri ile karşılaştırılır.

Sistem üç temel sağlık durumundan birini oluşturur:

- OK
- WARNING
- CRITICAL

Örneğin bir cihazda CPU, RAM veya disk kullanımı belirlenen eşikleri aşarsa ilgili problem health detector tarafından tespit edilir.

Bir cihaz tamamen erişilemez hale geldiğinde ise:

- DEVICE UNREACHABLE

durumu oluşturulur.

Threshold değerleri ayrı bir configuration yapısında tutulduğu için sistemin davranışı merkezi olarak değiştirilebilir.

### Investigation

RemoteSysWatch'in önemli özelliklerinden biri, bir problem tespit edildiğinde yalnızca problemi bildirmekle yetinmemesidir.

Örneğin:

```text
CPU yüksek
    ↓
Top processler
    ↓
PID / Process adı / CPU kullanımı
    ↓
Load bilgisi
    ↓
İlgili sistem logları
    ↓
Possible Cause
```

RAM problemi oluştuğunda:

```text
RAM yüksek
    ↓
Top RAM kullanan processler
    ↓
Bellek durumu
    ↓
Swap / Pagefile
    ↓
İlgili sistem olayları
```

Disk probleminde:

```text
Disk yüksek
    ↓
Hangi disk / mount?
    ↓
Toplam / kullanılan / boş alan
    ↓
Gerekli durumlarda kullanım detayları
    ↓
İlgili sistem olayları
```

Servis problemlerinde ilgili servisin durumu ve sistem olayları incelenebilir.

Bu sayede sistemin amacı yalnızca:

> "CPU yüksek."

demek değil;

> "CPU yüksek ve hangi processlerin bu duruma katkıda bulunduğu konusunda ek bilgi sağlamak."

seviyesine çıkmaktır.

Possible Cause alanı kural tabanlı ve heuristik bir yaklaşımla oluşturulur. Bu nedenle kesin bir root-cause analysis sonucu değil, toplanan sistem verilerine dayanan olası neden bilgisidir.

### Linux Investigation

Linux tarafındaki investigation mekanizmaları problem türüne göre farklı bilgiler toplar.

Örneğin CPU problemi sırasında:

- PID
- Process adı
- CPU kullanımı
- RAM kullanımı
- Load Average
- CPU çekirdek sayısı

gibi bilgiler incelenebilir.

RAM problemlerinde process ve swap kullanımı kontrol edilir.

Disk problemlerinde ilgili mount ve disk kullanım bilgileri incelenebilir.

Sistem olayları için ortam ve işletim sistemi sürümüne bağlı olarak:

- journalctl
- dmesg
- syslog

gibi kaynaklardan bilgi alınabilir.

### Windows Investigation

Windows tarafında problem türüne göre sistemden ek bilgiler alınabilir.

CPU problemlerinde:

- Process adı
- PID
- CPU kullanımı
- Logical core sayısı

gibi bilgiler incelenebilir.

RAM problemlerinde:

- Top processler
- Toplam RAM
- Boş RAM
- Pagefile kullanımı

gibi bilgiler alınabilir.

Disk problemlerinde ilgili sürücülerin:

- Boyutu
- Boş alanı

bilgileri kontrol edilir.

Ayrıca Windows sistem olayları için klasik Event Log mekanizmalarından yararlanılır.

Windows 7 gibi legacy sistemlerin bulunması nedeniyle modern Windows sistemlerine özgü özelliklere tamamen bağımlı kalmayan yöntemler tercih edilmiştir.

### Erişilebilirlik Kontrolü

Bir cihaz erişilemez olduğunda yalnızca SSH veya WinRM bağlantısını tekrar tekrar denemek yerine ağ bağlantısı ayrıca kontrol edilebilir.

Monitoring sunucusu üzerinden:

- ICMP ping
- Latency
- Route
- TCP erişilebilirliği

kontrol edilebilir.

Örnek bir durum:

```text
🚨 ALERT [CRITICAL]

Cihaz: win11ent
Sorun: DEVICE UNREACHABLE

Target: 192.168.x.x
Latency: ...

Route to Target:
...

TCP Probe:
erişilemedi

Possible Cause:
Hedef cihaz veya bağlantı yolunda problem olabilir.
```

Bu yaklaşımda hedef zaten erişilemez durumdaysa tekrar tekrar SSH/WinRM ile bağlanmaya çalışmak yerine, monitoring sunucusunun hedefe giden bağlantısını değerlendirmek amaçlanır.

### Telegram Bildirimleri

Tespit edilen problemler Telegram Bot API üzerinden bildirilir.

**ALERT**

Bir problem ilk kez tespit edildiğinde:

```text
🚨 ALERT [CRITICAL]

Cihaz: ubuntu18
Sorun: CPU 100.0%

Detay:

Problem: High CPU Usage
Cores: 1
Load Average: ...

Top Process:
stress-ng-cpu → 97.3% CPU

Possible Cause:
CPU'nun büyük kısmını tek bir process tüketiyor.
```

**Disk Alert**

```text
🚨 ALERT [WARNING]

Cihaz: win10pro
Sorun: Disk 84.15%

Detay:

Problem: High Disk Usage
Drive: C:
Size: 31.3 GB
Free: 5 GB

Possible Cause:
C: sürücüsü en dolu sürücü.
```

**Recovery**

Bir problem normale döndüğünde:

```text
✅ RECOVERY [OK]

Cihaz: ubuntu26
Sistem normale döndü.
```

### State Management

Bir problemin her monitoring döngüsünde tekrar Telegram'a gönderilmesi gereksiz spam oluşturabilir.

Bu nedenle cihazların önceki sağlık durumu takip edilir.

Örnek:

```text
Problem yok
    ↓
WARNING
    ↓
ALERT gönder

Problem devam ediyor
    ↓
Yeni ALERT gönderme

Problem düzeliyor
    ↓
OK
    ↓
RECOVERY gönder
```

State yönetimi cihaz bazında gerçekleştirilir.

Böylece bir cihazdaki problem diğer cihazların bildirim durumunu etkilemeden ayrı şekilde takip edilebilir.

---

## Ana Monitoring Döngüsü

Sistem sürekli çalışan bir monitoring döngüsü üzerinden çalışır.

Temel akış:

```text
                START
                  ↓
        10 cihazdan veri topla
                  ↓
         Health Detection
                  ↓
          Problem var mı?
             /          \
           Hayır        Evet
             │            │
             │      Investigation
             │            │
             │        Diagnosis
             │            │
             └──────┬─────┘
                    ↓
               State Manager
                    ↓
               Telegram
                    ↓
             Yeni döngü
```

Linux ve Windows sistemler paralel olarak sorgulanarak monitoring döngüsünün daha verimli çalışması hedeflenmiştir.

---

## Test Ortamı

RemoteSysWatch geliştirme ve test sırasında VMware Workstation Pro üzerinde oluşturulan sanal makineler kullanılarak çalıştırılmıştır.

Toplam ortam:

- 5 Linux
- 5 Windows
- 1 Monitoring Server

**= 11 sanal makine**

10 hedef cihazın farklı işletim sistemi sürümleri kullanması özellikle test kapsamını genişletmek amacıyla tercih edilmiştir.

---

## Test Edilen Senaryolar

Sistem geliştirilirken farklı hata durumları kontrollü şekilde oluşturularak test edilmiştir.

**CPU**
- Linux üzerinde yüksek CPU kullanımı
- CPU kullanan processlerin tespiti
- WARNING / CRITICAL üretimi
- Telegram ALERT

**RAM**
- Yüksek RAM kullanımı
- Yüksek RAM kullanan processlerin incelenmesi
- Linux swap kontrolü
- Windows pagefile kontrolü
- Telegram ALERT

**Disk**
- Disk threshold'unun aşılması
- İlgili drive / mount bilgilerinin alınması
- Telegram ALERT

**Connectivity**
- Cihazın erişilemez hale getirilmesi
- Ping kontrolü
- Route kontrolü
- TCP probe
- DEVICE UNREACHABLE alarmı

**Recovery**
- Problem oluşturulması
- ALERT gönderilmesi
- Problemin düzeltilmesi
- Otomatik RECOVERY gönderilmesi

**Legacy Uyumluluğu**
- Ubuntu 18.04
- Windows 7
- Diğer Linux ve Windows sürümleri

üzerinde remote monitoring mekanizmaları test edilmiştir.

Detaylı test notları için: [docs/TESTS.md](docs/TESTS.md)

---

## Geliştirme Sırasında Karşılaşılan Problemler

### 1. Kaynak Kullanımı

10 hedef sistem ve 1 monitoring server aynı fiziksel host üzerinde VMware ile çalıştırıldı.

32 GB RAM'e sahip host üzerinde toplam sanal makine sayısı nedeniyle ciddi bellek baskısı oluştu. VM'lerin RAM miktarları farklı işletim sistemlerinin ihtiyaçları dikkate alınarak yeniden dağıtıldı ve sonuç olarak 10 hedef sistem + monitoring server aynı ortamda çalıştırılabilir hale getirildi.

Bu süreç, yalnızca yazılım tarafında değil, monitoring sisteminin çalıştığı test altyapısının da planlanması gerektiğini gösterdi.

### 2. Legacy İşletim Sistemi Desteği

Windows 7 ve Ubuntu 18.04 gibi eski sistemlerde modern komutların veya araçların bulunmaması nedeniyle farklı yöntemlerin ve fallback mekanizmalarının kullanılması gerekti.

### 3. Investigation Detaylarının Boş Gelmesi

İlk aşamalarda bazı Telegram mesajlarında `Detay:` alanının boş kaldığı görüldü.

Sorunun investigation katmanındaki problem sınıflandırmasından kaynaklandığı tespit edildi.

Problem türlerinin daha güvenilir şekilde sınıflandırılması ve her problem için ayrı investigation akışlarının oluşturulmasıyla bu sorun giderildi.

---

## Proje Yapısı

```text
RemoteSysWatch/
│
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── main.py
│
├── collectors/
│   ├── __init__.py
│   ├── linux_collector.py
│   └── windows_collector.py
│
├── config/
│   ├── __init__.py
│   ├── devices.py
│   ├── windows_devices.py
│   ├── thresholds.py
│   └── telegram.py
│
├── detectors/
│   └── health_detector.py
│
├── investigators/
│   └── detective.py
│
├── models/
│   └── device_data.py
│
├── notifiers/
│   └── telegram.py
│
├── utils/
│   └── state_manager.py
│
├── tests/
│   ├── test_linux_collector.py
│   ├── test_all_linux.py
│   ├── test_winrm_collector.py
│   └── test_all_windows.py
│
└── docs/
    ├── ARCHITECTURE.md
    ├── TESTS.md
    └── screenshots/
        ├── architecture.png
        ├── cpu-alert.png
        ├── disk-alert.png
        ├── unreachable-alert.png
        └── recovery.png
```

---

## Teknik Bileşenler

- **Python** — Ana uygulama mantığı Python ile geliştirilmiştir.
- **Paramiko** — Linux sistemlere SSH üzerinden bağlanmak ve uzaktan komut çalıştırmak için kullanılır.
- **WinRM** — Windows sistemlerden uzaktan veri toplamak için kullanılır.
- **PowerShell / WMI** — Windows sistemlerde CPU, RAM, disk, servis ve sistem olayları gibi bilgilerin alınmasında kullanılır.
- **Telegram Bot API** — Alarm ve recovery bildirimlerinin gönderilmesi için kullanılır.
- **VMware Workstation Pro** — 10 hedef sistem ve monitoring server'dan oluşan geliştirme/test ortamının oluşturulmasında kullanılmıştır.

---

## Kurulum

Projeyi klonladıktan sonra gerekli Python paketleri kurulabilir:

```bash
pip install -r requirements.txt
```

Monitoring sunucusunun hedef Linux sistemlere SSH, Windows sistemlere ise WinRM üzerinden erişebilmesi gerekir.

Telegram bildirimleri kullanılacaksa bot bilgileri güvenli bir configuration/environment yapısı üzerinden sağlanmalıdır.

> Gerçek şifreler, SSH anahtarları, Telegram bot tokenları ve diğer özel bilgiler repository içerisinde tutulmamalıdır.

---

## Güvenlik

Public bir repository oluşturulacağı için gerçek kimlik bilgileri source code içerisinde tutulmamalıdır.

Örneğin `.env` gibi dosyalar `.gitignore` ile repository dışında tutulabilir.

Repository'ye ise `.env.example` gibi örnek configuration dosyaları eklenebilir.

Aynı şekilde gerçek cihaz bilgileri yerine örnek veya maskelenmiş değerler kullanılmalıdır.

---

## Sınırlamalar

RemoteSysWatch öncelikle laboratuvar, öğrenme ve teknik portföy amacıyla geliştirilmiş bir monitoring projesidir.

Henüz:

- yüzlerce veya binlerce cihazlık büyük ortamlarda,
- dağıtık monitoring server mimarisinde,
- yüksek erişilebilirlik gerektiren production ortamlarında

test edilmemiştir.

Investigation katmanı kural tabanlı ve heuristik bir yapıya sahiptir. Sistem tarafından oluşturulan Possible Cause bilgileri kesin bir root-cause analysis sonucu olarak değerlendirilmemelidir.

---

## Dokümantasyon

Projeye ait teknik detaylar `docs/` klasöründe tutulmaktadır.

- [Mimari](docs/ARCHITECTURE.md)
- [Testler](docs/TESTS.md)

Test scriptleri ise `tests/` klasöründe bulunmaktadır.

---

## Proje Durumu

**Tamamlandı.**

RemoteSysWatch'in temel monitoring, detection, investigation, notification ve recovery akışı çalışır durumdadır.

- Remote Collection — ✅
- Linux Monitoring — ✅
- Windows Monitoring — ✅
- CPU Monitoring — ✅
- RAM Monitoring — ✅
- Disk Monitoring — ✅
- Connectivity Detection — ✅
- Health Detection — ✅
- Investigation — ✅
- Diagnosis — ✅
- Telegram ALERT — ✅
- Telegram RECOVERY — ✅
- State Management — ✅
- 10 Device Monitoring — ✅

---

## Sonuç

RemoteSysWatch ile merkezi bir Python monitoring sunucusunun;

```text
Uzak sistemlere bağlanması
        ↓
Sistem bilgilerini toplaması
        ↓
Sağlık durumunu analiz etmesi
        ↓
Problem oluştuğunda inceleme yapması
        ↓
Probleme ilişkin ek bilgi üretmesi
        ↓
Telegram üzerinden ALERT göndermesi
        ↓
Problem düzeldiğinde RECOVERY göndermesi
```

uçtan uca gerçekleştirilmiştir.

Proje boyunca Python, Linux, Windows, SSH, WinRM, PowerShell, WMI, Telegram Bot API ve VMware gibi farklı teknolojiler tek bir monitoring sistemi içerisinde bir araya getirilmiştir.

---

## Geliştirici

**Muhammed Emir Zindan**

Python • Linux • Networking • Systems • Automation

Bu proje öğrenme, geliştirme ve teknik portföy amacıyla oluşturulmuştur.
