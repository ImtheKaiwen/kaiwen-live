# Kaiwen Live — Türkçe Gerçek Zamanlı, Yerel Speech-Native Masaüstü Asistanı

> **Belge türü:** Ürün README'si, teknik mimari rehberi, geliştirme sözleşmesi ve V1 teslim planı.<br>
> **Repository:** [`ImtheKaiwen/kaiwen-live`](https://github.com/ImtheKaiwen/kaiwen-live)<br>
> **Hedef:** Türkçe, öncelikle tek kullanıcı, Windows masaüstü, local-first, düşük gecikmeli voice-to-voice deneyimi.<br>
> **Durum:** `TASARIM / PLANLAMA` — GitHub reposunda 30 Ekim 2026 incelemesi itibarıyla yalnız kısa başlangıç `README.md` vardır; bu belgede çizilen uygulama, UI, sidecar ve streaming API **henüz geliştirilmemiştir**.<br>
> **Ana bağımlılıklar:** Kaiwen Speech, sürümlü Forge model release'leri ve isteğe bağlı Kaiwen Agent; UI için Kaiwen Design.<br>
> **Kanonik belge ilişkisi:** Bu README ürün kapsamını ve uygulama sırasını tanımlar; protokol ayrıntıları [Workspace Integration](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/INTEGRATION.md), [Speech Streaming](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/STREAMING.md), [Speech API](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/API.md), [Forge Registry](https://github.com/ImtheKaiwen/kaiwen-forge/blob/8bf2af3b925bc1478328b4a26fcba36af74480fb/docs/MODEL_REGISTRY.md) belgelerindedir.

> **D1 belge entegrasyonu:** Upstream başlangıç tanımı — “Real-time, speech-native AI assistant powered by Kaiwen Speech and Kaiwen Agent.” — ürün niyeti olarak korunur; iki satırlık orijinal README [`README.upstream-20261030.md`](README.upstream-20261030.md) yolunda byte-for-byte mevcuttur. Bu ana belgede anlatılan Electron uygulaması, sidecar ve streaming API hâlâ **TASARIM / PLANLAMA** durumundadır.

---

## 1. Kaiwen Live nedir ve ne değildir?

Kaiwen Live, kullanıcının bilgisayarındaki mikrofon üzerinden Türkçe konuştuğu; modelin yerel olarak konuşma sesini işlediği ve yanıtını hoparlöre ses olarak verdiği **masaüstü ürün katmanıdır**. Bir araştırma modelini kullanılabilir bir günlük arayüze çevirmek onun işidir. Mikrofonu yönetmek, ses çıktısının gerçekten duyulmasını sağlamak, bir kullanıcının konuşmaya yeniden girdiğini fark edip eski yanıtı kesmek, modelin yüklenmesini izlemek ve hataları kullanıcıya anlaşılır göstermek bu ürünün özündedir.

Kaiwen Live **bir dil modeli eğitmez**; yeni codec veya Transformer yazmaz; dataset hazırlamaz; Forge'un deney scheduler'ını ya da Agent'ın araç yürütme motorunu kopyalamaz. Speech'in public inference yüzeyini tüketir. Forge'dan sürümlü ve doğrulanmış yayın artifact'i alır. Agent'a yalnızca açıkça tanımlı, izin verilmiş ve gerçekten desteklenen istekler yönlendirir.

İlk sürümün birincil başarı senaryosu: tek Windows kullanıcısı uygulamayı açar, kurulu modeli seçer, mikrofon yetkisini verir, Türkçe bir sesli soru sorar, konuşma bitişini bildirir veya güvenilir VAD yardımıyla turu bitirir, yerel modelden gelen ses yanıtını dinler, gerektiğinde durdurur ve uygulamayı kararlı biçimde kapatır. V1'de tam çift yönlü eşzamanlı konuşma garanti edilmez. **Native streaming** ayrı, ölçüm gerektiren bir kilometre taşıdır.

### 1.1 İşleyen ürün ile araştırma hedefi ayrı tutulur

- **Mevcut ve doğrulanmış temel:** `kaiwen-speech` Python kodunda `kaiwen_voice` import paketi, Mimi referans codec'i, Transformer, checkpoint okuyucu, WAV tabanlı sıra ile inference ve temel benchmark scriptleri bulunur. Bu, masaüstü Live uygulamasının çalıştığı anlamına **gelmez**.
- **Hedef ürün:** Electron + React + TypeScript ön yüz; güvenli Electron main/preload köprüsü; Python Speech sidecar; mikrofon/hoparlör cihaz soyutlaması; turn yönetimi; ses kuyrukları; gözlemlenebilir metrikler; model installer.
- **Deneysel araştırma:** Kaiwen'e özgü codec, cached incremental inference, gerçek zamanlı Türkçe doğal konuşma, 2 GB VRAM sınıfı cihaz desteği, yüksek kalitede barge-in, eşzamanlı turn-taking.
- **Gelecek özellik:** Agent tarafından araç kullanımı ve doğrulanmış dış bilgilerle yanıt. Bu, saf speech-native hızlı yolun ön şartı değildir.

İşlevsellik kullanıcı arayüzünde `available`, `experimental`, `unavailable` olarak gösterilir. Kullanıcıya native streaming varmış izlenimi veren, fakat aslında tek WAV üreten bir demo **yanlış etiketlenmiş** sayılır.

### 1.2 Bir cümlelik ürün vaadi

> **Türkçe konuş; uygun yerel modelle sesli cevap al; neyin çalıştığını, neyin beklediğini ve neyin başarısız olduğunu açıkça gör.**

Bu vaat, sıfır gecikme veya her soruya doğru cevap garantisi içermez. Kullanıcı deneyimi yalnız model kalitesine değil ses cihazına, driver'a, kuyruk gecikmesine ve model artifact'inin gerçek performansına bağlıdır.

## 2. Tasarım ilkeleri ve başarı kriterleri

1. **Speech-first:** Ürünün normal konuşma yolu `audio → speech codec → speech model → speech codec → audio` olacak; gizli `STT → text LLM → TTS` pipeline'ı speech-native diye pazarlanmayacaktır.
2. **Local-first:** İlk demo mikrofon/ses inference için internete bağlı olmamalı. Modelin ilk indirilmesi veya açıkça seçilen Agent görevi ayrıca ağ kullanabilir.
3. **Fast path kısa olsun:** Her kullanıcı turu API aracına, RAG'e, web aramasına veya metin transkriptine mecbur bırakılmayacak.
4. **Gerçek işaretler:** `microphone_listening`, `model_generating`, `audio_playing` birbirinden ayrılacak; hareketli dalga formu tek başına çalışıyor kanıtı değildir.
5. **Durdurulabilirlik:** Mikrofonu kapatma, oynatmayı susturma, generation iptali ve session kapatma farklı kontroller olacak.
6. **Doğru kaynak sahipliği:** Ağır inference renderer'da veya audio callback thread'inde yapılmayacak. GPU modelinin bir sahibi olacak.
7. **Geri kazanılabilirlik:** Sidecar çökmesi uygulamayı zorunlu olarak çökertmeyecek; kullanıcı açık hata ve yeniden deneme seçeneği görecek.
8. **Sürüm güvenliği:** Her release dosya bütünlüğü ve codec–Transformer uyumu doğrulanarak kurulacak. `latest` etiketi tek başına güven kanıtı değildir.
9. **Veri mahremiyeti:** Ses varsayılan olarak bir sunucuya gönderilmeyecek ve otomatik olarak kalıcı arşive yazılmayacak.
10. **Ölçüm:** Gecikme, VRAM, RTF, oynatma underrun ve sıcak/soğuk model açılışı ölçülmeden başarı iddiasına dönüştürülmeyecek.
11. **İlk entegrasyonu önce bitir:** Tek kullanıcı, tek model, tek Windows cihazı ve tek tur konuşma düzgün çalışmadan multi-user, cloud streaming veya telefon entegrasyonu açılmayacak.
12. **Modüler, fakat gerçekçi:** Soyutlamalar kod tekrarını veya gerçek değişkenliği çözdüğü ölçüde yapılacak; on sağlayıcılı boş interface koleksiyonu hedef değildir.

### 2.1 Kabul seviyeleri

| Seviye | Kullanıcıya dürüst etiket | Gerekli kanıt |
|---|---|---|
| L0 | `UI Prototype` | UI açılır; ses ve model işlemleri simülasyon olarak etiketlenir. |
| L1 | `Audio Loopback` | Gerçek mikrofon kaydı hoparlöre geri döndürülebilir; cihaz değişimi ve stop testi vardır. |
| L2 | `Batch Speech Demo` | Gerçek Speech checkpoint + codec ile WAV → WAV yanıt; kalite beklentisi ayrıca raporlanır. |
| L3 | `Chunked Playback` | Gerçek audio chunk taşıma ve tampon; model kısmen batch olabilir, etiket bunu açıklar. |
| L4 | `Native Streaming Experimental` | Cached incremental model/codec parçalı ses üretir, parity ve ses testleri geçer. |
| L5 | `Voice Assistant Pilot` | Tek kullanıcı için cihaz, kesme, uzun oturum, bütünlük ve ölçümlü kalite eşikleri geçer. |
| L6 | `Agent-Enabled Pilot` | İzinli Agent görevleri ayrı ve güvenli yol üzerinden tamamlanır; metinden sese dönüş kanıtlıdır. |

`L3`, `L4` veya `L5` seviyesinin tamamı README yazıldığı için gerçekleşmiş sayılamaz. Sadece gerçek uygulama ve kaydedilmiş test kanıtıyla statü değişir.

## 3. Repository ekosistemi ve bağımlılık yönleri

```text
kaiwen-ai/                            # Lokal koordinasyon workspace'i; ayrı git repo değil
├── docs/                             # Ortak sözleşmeler
├── kaiwen-speech/                    # Codec, Transformer, inference, streaming SDK hedefi
├── kaiwen-forge/                     # Eğitim, deney, değerlendirme, model registry hedefi
├── kaiwen-corpus/                    # Veri hazırlığı ve export
├── kaiwen-live/                      # Bu repo: masaüstü uygulaması ve ses I/O
├── kaiwen-design/                    # Ortak React/TS tasarım sistemi
└── kaiwen-agent/                     # Opsiyonel Agent yürütme altyapısı
```

Bunlar altı bağımsız GitHub repositoriesidir; `kaiwen-ai/` lokal parent dizini yeni bir monorepo veya GitHub süper-repo değildir. Her repo kendi sürümleme, CI, bağımlılık ve release kararını bağımsız alır.

| İlişki | Sorumluluk | Kesin sınır |
|---|---|---|
| Live → Speech | Local inference, model/codec yeteneği, audio output | Live model katmanları yazmaz, Speech işletim sistemi mikrofonu açmaz. |
| Forge Registry → Live | Sürümlü model release artifact, manifest, doğrulama | Live training checkpoint'ini doğrudan "stable" ilan etmez. |
| Live → Design | UI bileşenleri, temalar, erişilebilirlik | Tasarım sistemini kopyalayıp iki ayrı kütüphane oluşturmaz. |
| Live → Agent | İsteğe bağlı bilgi/araç görevleri | Agent çağrısı audio hızlı yolunu bloklamaz. |
| Corpus → Forge → Live | Veri → eğitim → değerlendirme → release | Live ham dataset'i veya eğitim loglarını çekerek inference yapmaz. |

Gelecekte Agent'ın `text` yanıtını Live'ın seslendirmesi gerekirse bunun **ayrı bir text-to-audio köprüsü** ile kanıtlanması gerekir. Mevcut speech-native Transformer'ın düz metni koşullayabildiği iddia edilmez. Bu detay [Agent sınırı](#22-agent-entegrasyonu-ve-metin-yanıt-sorunu) başlığında ele alınır.

## 4. Mevcut kod envanteri: uygulama statüsü

**Kontrol edilen GitHub repository:** `ImtheKaiwen/kaiwen-live`, `main`, 30 Ekim 2026. Repository ağacında yalnız `README.md` bulunmuştur. `apps/desktop`, `apps/sidecar`, `package.json`, `pyproject.toml`, testler veya CI workflow henüz mevcut değildir.

**Speech tarafı mevcut olanlar:** Python dağıtım adı `kaiwen-voice`, import kökü `kaiwen_voice`, mevcut `MimiCodec`, `KaiwenSpeechTransformer`, `load_checkpoint`, `build_dialogue_prompt`, `generate` ve `scripts/infer_audio.py`. Bunlar turn-based referans inference sağlar. `generate()` tam öneki tekrarlı hesaplar; native streaming, KV cache veya gerçek SDK session API'si mevcutmuş gibi davranılmamalıdır.

**Forge tarafı:** Model Registry README/şartnamesi hazırdır, fakat production registry'nin çalışan indirme/activation servisi henüz yoktur. **Design ve Agent:** Ayrı kütüphanelerin varlığı Live ile entegrasyonun bittiği anlamına gelmez; gerçek paket sürümü, API ve yetenekleri entegrasyon anında kontrol edilmelidir.

Ürün README'sindeki örnek `kaiwen-live` CLI komutları, dizinleri ve arayüzleri **HEDEF** olarak verilir. Gerçek kaynak kodu eklenip test edilene kadar `npm run dev`, `pnpm dev` veya `uv run ...` komutları bu repo için çalışır diye gösterilmez.

### 4.1 Hızlı statü tablosu

| Bileşen | Bugünkü durum | V1 önceliği |
|---|---|---|
| Electron kabuğu | Yok | Birinci aşama |
| React/TS arayüzü | Yok | Birinci aşama |
| Kaiwen Design entegrasyonu | Yok | Erken aşama |
| Mikrofon/hoparlör loopback | Yok | Birinci çalışır demo |
| Speech sidecar başlatma | Yok | Erken aşama |
| Real model WAV→WAV | Speech script'inde var, Live'a bağlı değil | Pilot |
| Chunked IPC / stream | Yok | Sonraki aşama |
| Native KV cache inference | Speech'te hedef | Ayrı araştırma kilometre taşı |
| Agent bridge | Yok | Opsiyonel, geç aşama |
| Model registry installer | Forge'da tasarım | İkinci faz |
| Windows CI/release | Yok | Her prototipten itibaren artan kapsam |

## 5. Hedef teknoloji seçimi ve nedenleri

İlk platform **Windows 10/11** ve Türkçe arayüzdür; Linux/macOS mimari açıdan mümkün tutulur fakat V1 teslim koşulu değildir. Kullanıcıya kurulabilir tek masaüstü uygulama sunulur, Python inference ise ayrı bir process olarak çalışır. Amaç Electron'un görünümü yönetmesi, Python'un hesaplama yapmasıdır.

| Katman | Önerilen teknoloji | Karar gerekçesi |
|---|---|---|
| Desktop main/preload | Electron + TypeScript | Pencere, native izin, uygulama yaşam döngüsü ve güvenli IPC |
| UI | React + TypeScript + Vite | Modüler, hızlı geliştirme; Design ile uyum |
| Tasarım | `kaiwen-design` | Tek görsel kaynak, kendi bileşenini kopyalamama |
| UI state | Hafif store; başlangıç için Zustand opsiyonel | Event kaynaklarını render state'inden ayırma |
| Backend sidecar | Python 3.11+ | Mevcut `kaiwen_voice`, PyTorch ve ses kütüphaneleriyle entegrasyon |
| Audio I/O | Doğrulanmış native kütüphane/modül | Düşük gecikmeli cihaz açma, callback, Windows WASAPI değerlendirmesi |
| IPC control | Lokal named pipe veya yetkili localhost kanalı | Session, event, komut ve hata protokolü |
| IPC audio | Binary PCM frame taşıma | JSON/base64 yükünü ses hızlı yoluna sokmama |
| Kalıcı ayarlar | Kullanıcı veri dizininde atomik, sürümlü config | Model seçimi, ses cihazları, izin ve tema |
| Günlükleme | Yapılandırılmış yerel log | Debug ve performans; ses içeriği saklamadan |
| Installer | Electron Builder / Windows NSIS adayı | Paketlenmiş sidecar, model yönetimi, rollback |

**Audio kütüphanesi sonradan benchmark ile seçilir.** Web Audio, native Node modülü ve Python `sounddevice` gibi seçenekler fiziksel cihaz, sürücü, örnekleme formatı ve IPC gecikmeleriyle karşılaştırılmadan tek doğru ilan edilmez. Eğer mikrofon yakalama Electron renderer'dan yapılıyorsa `getUserMedia` izin akışı ve web audio callback çalışma biçimi; native taraftaysa OS permission ve callback yaşam döngüsü ayrı test edilir.

### 5.1 Paket yöneticisi ve build stratejisi

Web UI için `pnpm` kullanılabilir; Python tarafı `uv` ile ayrı kilitlenebilir. Belge bu iki aracı gelecekte kurulacak standart **önerisi** olarak ele alır. Dependency lock, Windows CI, Python ABI ve inference sidecar artifact'i birlikte test edilmeden kullanıcılara tek bir `exe` yeterliymiş gibi dağıtım sözü verilmez.

## 6. Hedef klasör yapısı — bugün GitHub'da yok

```text
kaiwen-live/
├── README.md
├── AGENTS.md                           # Sonraki dokümantasyon dosyası
├── docs/
│   ├── ARCHITECTURE.md                  # Sonraki dokümantasyon dosyası
│   ├── DESIGN_AND_UX.md                 # Sonraki dokümantasyon dosyası
│   └── AGENT_INTEGRATION.md             # Sonraki dokümantasyon dosyası
├── apps/
│   ├── desktop/
│   │   ├── electron/
│   │   │   ├── main.ts
│   │   │   ├── preload.ts
│   │   │   ├── audio-device-manager.ts
│   │   │   ├── runtime-supervisor.ts
│   │   │   └── security/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── features/
│   │   │   │   ├── conversation/
│   │   │   │   ├── devices/
│   │   │   │   ├── models/
│   │   │   │   ├── settings/
│   │   │   │   └── diagnostics/
│   │   │   ├── components/
│   │   │   └── state/
│   │   └── package.json
│   └── sidecar/
│       ├── pyproject.toml
│       ├── src/kaiwen_live_runtime/
│       │   ├── app.py
│       │   ├── protocol/
│       │   ├── adapters/
│       │   ├── sessions/
│       │   ├── audio/
│       │   ├── models/
│       │   └── telemetry/
│       └── tests/
├── packages/
│   └── contracts/                       # TS sözleşmeler; backend için ayrıca doğrulanır
├── configs/
│   └── runtime.example.yaml
├── tests/
│   ├── contract/
│   ├── e2e/
│   ├── fault_injection/
│   └── fixtures/
├── scripts/
├── .github/workflows/
└── docs/decisions/                      # Gerekirse ADR'lar
```

Bu ağaç **mimari başlangıç önerisidir**. İlk PR'da tüm klasörlerin boş iskeletini oluşturmak zorunlu değildir. Testi olmayan sahte modüller yerine işleyen dar bir dikey dilim üretmek tercih edilir.

## 7. Çalışma zamanının üst düzey akışı

```text
User speech
   │
   ▼
Microphone + OS permission              (Live)
   │ PCM + timestamps
   ▼
Capture queue + resample/normalize      (Live audio transport)
   │ bounded binary PCM chunks
   ▼
Turn controller                         (Live)
   │ turn-end / typed control events
   ▼
Speech runtime adapter                  (Live sidecar → Speech SDK)
   │ codec → model → codec
   ▼
Audio output chunks / events            (Speech sidecar)
   │ stream ID + generation ID
   ▼
Playback queue + jitter buffer          (Live)
   │ PCM output device
   ▼
User hears Turkish response
```

Burada iki ürün ayarı vardır: **`batch_turn`** ve **`native_stream`**. `batch_turn`, konuşma turu bitince toplu yanıt üretir; `native_stream`, Speech'in gerçek incremental üretimi hazır olduğunda etkinleşir. `fake_runtime`, UI ve IPC testleri için üçüncü bir test modudur. Bu mod konuşma modelinin gerçek yetenekleri olarak sunulmaz.

### 7.1 Hızlı konuşma yolu ile Agent yolu

Sesli bir soruya, modelin öğrendiği örüntülerden yanıt verme **Fast Path**'tir. Bilinmeyen güncel bilgi, saat, internet araması veya dosya işlemi gibi doğrulama/araç gerektiren görev, açık intent ve yetenek sözleşmesiyle **Agent Path** olabilir. Agent isteğinin varlığı hızlı ses yolundaki mikrofon ve playback kontrolünün sahibi olmasını değiştirmez.

Speech Transformer ses tokenlarından kendiliğinden `agent_requested` üretiyormuş gibi davranılamaz. Sinyal kaynağı seçilip güvenilirlik düzeyi belgelenir: kullanıcı elle Agent modu seçebilir, gelecekte modelin eğitilmiş özel tokenları olabilir veya opsiyonel bir intent detector devreye girebilir. Bu üçü birbirinin yerine geçmez.

## 8. Ses I/O: format, kanallar ve saat alanları

Ses işleme sözleşmesi **explicit** olacak: mikrofonun fiziksel formatı, taşıma formatı, codec'in beklediği format ve hoparlörün çıkış formatı ayrı kaydedilecek. Fiziksel cihaz çoğu zaman 48 kHz olabilir; mevcut Mimi referansı **24 kHz** ses bekler ve codec'e gönderilen sample rate yanlışsa hata üretir. Resampling yapılması Live/adapter sınırında açık, testli bir işlem olmalıdır.

| Alan | Örnek başlangıç profili | Kritik kural |
|---|---|---|
| Capture hardware | Cihazın native 44.1/48 kHz formatı | Donanım desteklerini sorgula; zorla varsayma. |
| Canonical transport | 24 kHz mono PCM float32 veya PCM16 | Çerçeve başına format bildir; anlaşma olmadan gönderme. |
| Mimi codec referansı | 24 kHz, ~12,5 temporal frame/s, 8 codebook, 2048 vocab | Kendi codec'in 50 Hz/4×1024 tasarımı **henüz deneysel**. |
| Playback device | Desteklediği sample rate ve channel layout | Yeniden örnekleme/mono→stereo dönüşümü açık yap. |
| Chunk duration | Ölçülecek; ör. 20 ms capture penceresi | Bu bir deney parametresidir, native model frame'i değildir. |
| Timebase | Sample index + monotonic nanoseconds | Wall clock ile audio sample zamanını karıştırma. |
| Buffer | Süre cinsinden sınırlı, ör. deneysel 100–300 ms | Gerçek gecikme ölçümüyle ayarla; sınırsız kuyruk yok. |

PCM16 hesabı: 24.000 örnek/s × 1 kanal × 2 bayt/örnek = **48.000 bayt/s** ham payload. 20 ms'lik bir mono PCM16 parçası **960 bayt** taşır. Bu basit byte hesabı ağ/IPC header, codec output, resample ve gerçek cihaz tamponlarını **içermez**. PCM float32 kullanılırsa aynı örneğin payload'ı iki katına çıkar.

### 8.1 Capture thread'i için yasaklar

Cihaz callback'inde PyTorch inference, disk yazma, network fetch, JSON parse, ağır mutex, dinamik büyük allocation veya React state güncellemesi yapılmaz. Callback yalnız kısa blok işlemesi, timestamp ve bounded ring-buffer push için kullanılır. Kaydedilemeyen veya yetişmeyen ses parçaları sessizce kaybolduğunda metrik üretilmelidir.

### 8.2 AEC, gürültü ve yanlış barge-in

Hoparlörden gelen sesin mikrofona geri dönmesi, kullanıcının konuştuğu sanılabilir. V1'de half-duplex/explicit turn-end sağlıklı bir referans olabilir; sonra OS echo cancellation, kulaklık profili, VAD ve gerçek barge-in birlikte test edilir. Barge-in sistemini yalnız bir enerji eşiğine bağlamak yankıyı kullanıcı sesiyle karıştırabilir. `speaker separation` ve gerçek overlap tespiti henüz model tarafında kanıtlı değildir.

## 9. Oturum ve tur durum makinesi

Kanonik ortak yaşam döngüsü [Integration](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/INTEGRATION.md) ile uyumlu olmalı:

```text
created → initializing → ready → listening → processing → speaking
                              ↑                         │
                              └──── next turn ──────────┘
Any live state → closing → closed
Any operation failure → failed → explicit recovery or new session
```

Bu çizim yalnız okunabilir özet; her geçişin koşulu vardır. `created → speaking`, `closed → listening` ve `failed → speaking` doğrudan kabul edilmez. `ready` modelin doğrulanıp yüklendiğini, `listening` mikrofonun gerçekten callback aldığı durumunu, `processing` tur sonu sonrası inference'ı, `speaking` en azından playback kuyruğunda izinli ses çıktısı olduğunu ifade eder. "Yanıt hazır" ile "kullanıcı sesi duydu" farklı anlara karşılık gelir.

### 9.1 Kimliklerin anlamı

- `session_id`: Live ile Speech arasındaki tek konuşma oturumu; açılışta üretilir.
- `session_epoch`: Reset/cancel sırasında artan nesil; eski epoch'taki output playback'e giremez.
- `turn_id`: Kullanıcı konuşması ve yanıt eşleşmesi için mantıksal tur.
- `generation_id`: Bir yanıt üretme denemesinin kimliği; aynı turda retry yeni generation olabilir.
- `stream_id`: Belirli audio/control akışının kimliği.
- `sequence`: Akış içindeki artan paket sıra numarası; kayıp veya tekrar fark edilir.
- `correlation_id`: Tüm olay/trace boyunca sebep-sonuç izleme bilgisi.

**Kural:** `turn_id` ile `generation_id` veya `session_epoch` aynı değişken olarak kullanılmaz. Cihaz değişimi, iptal veya session reset sonrası eski paketleri engelleyen bariyer bu ayrımdır.

## 10. IPC protokolü: kontrol düzlemi ve ses veri düzlemi

Electron main/preload/renderer ile Python sidecar arasında kontrol olayları JSON olabilir; ses parçaları uzun base64 stringlere çevrilmemelidir. Bir localhost sunucusu seçilirse yalnız loopback'e bağlanmalı, gerçek origin yetkilendirilmeli, ephemeral port veya kilitli instance token kullanılmalı ve kurulan local port internete açık olmamalıdır. Named pipe seçilirse Windows ACL, izin ve yaşam döngüsü ayrı doğrulanır. Backend arayüzü renderer'a doğrudan sınırsız OS veya file-system yetkisi sunmaz.

**HEDEF event envelope örneği — mevcut çalışan implementasyon değil:**

```json
{
  "protocol_name": "kaiwen.live.session",
  "protocol_version": "1.0.0",
  "event_id": "evt-000042",
  "event_type": "generation.started",
  "session_id": "session-0001",
  "session_epoch": 0,
  "turn_id": "turn-0001",
  "generation_id": "gen-0001",
  "stream_id": "control-0001",
  "sequence": 42,
  "correlation_id": "trace-0001",
  "occurred_at_utc": "2026-10-30T14:00:00Z",
  "monotonic_ns": 123450000000,
  "payload": {
    "runtime_mode": "batch_turn",
    "model_release_id": "demo-unreleased"
  }
}
```

Bu örnek kimlikler test verisidir; gerçek release veya çalışan protokol olmadığını gösterir. Native IPC'deki binary chunk header'ı `magic/version`, `session_id`, `stream_id`, `sequence`, `session_epoch`, `generation_id`, `start_sample`, `sample_count`, `format_id`, `payload_length` gibi alanların sürümlü ve doğrulanabilir biçimde kodlanmasını gerektirir. **Header'ın byte layout'u henüz sabit değil**; ortak belge örneğini literal ikili protokol sanma.

### 10.1 Komutlar ve olaylar

| Yön | HEDEF olay/komut | Sahip | Not |
|---|---|---|---|
| UI → Live | `microphone.enable` | Live cihaz yöneticisi | OS izin kontrolü |
| UI → Live | `turn.finish` | Live turn controller | Açık tur sonu |
| UI → Live | `playback.stop` | Live playback | Son duyulacak sesin susturulması |
| Live → Speech | `generation.cancel` | Speech runtime | Yeni token üretiminin durdurulması |
| Live → Speech | `session.close` | Speech runtime | State ve VRAM temizliği |
| Speech → Live | `audio.chunk` | Speech/sidecar | Generation/epoch doğrulanır |
| Speech → Live | `generation.completed` | Speech/sidecar | Tüm sesin duyulduğu anlamına gelmez |
| Live → UI | `playback.started` | Live device manager | Device callback ile mümkün olduğunca yakın işaret |
| Live → UI | `playback.underrun` | Live device manager | Kullanıcıya kesik ses uyarısı gerekebilir |
| Sidecar → UI | `runtime.error` | Live supervisor | Tipli hata ve recovery önerisi |

Event isimleri **öneri**; [Speech API](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/API.md) ve shared contract testleri üzerinde tek enum hâline getirilecek. Örnek JSON payload, bitstream protokolünü tanımlamaz.

### 10.2 Backpressure ve sequence güvenilirliği

Ses callback'i için bounded input ring, sidecar için bounded transport queue ve playback için bounded output jitter buffer vardır. Tek bir sınırsız `asyncio.Queue` uzun oturumlarda kabul edilmez. Kuyruk büyümesi, stale frame drop, output underrun ve IPC gecikmesi ayrı sayılır. Audio paketinin yeniden gönderilmesi, sequence ve dönem bilgisini kontrol etmeden ikinci kez dinletilmesine neden olmamalıdır.

Yavaş UI render'ı ses akışına geri baskı uygulayamaz. Arayüz 60 FPS hedefine yetişemese bile audio callback kendi süre kısıtında çalışmalıdır. Gerektiğinde görsel waveform örnekleme sıklığı düşer, ses callback'inin önceliği düşürülmez.

## 11. Fake runtime, batch runtime ve native runtime

Live, gerçek model araştırması tamamlanmadan UI ve ses altyapısını ilerletebilmek için üç farklı runtime profiline ihtiyaç duyar:

| Profil | Gerçek input | Gerçek model | Gerçek streaming | Demo etiketi |
|---|---|---|---|---|
| `fake` | Gerçek/fixture mikrofon olabilir | Hayır | Hayır | `Simulation` |
| `batch_turn` | Evet | Kurulu uyumlu Speech checkpoint varsa evet | Hayır | `Batch inference` |
| `native_stream` | Evet | Evet | Evet, parity testli | `Experimental streaming` |

`fake` seçeneği cihaz ve UI state machine'i test eder: sabit orijinal test sesini döndürür veya açıkça sentetik/placeholder cevap gönderir. Her sahte PCM üretilmişse event'te `source=fixture` gibi kanıtlı değer taşır. `batch_turn` profilinde kullanıcı konuşması bitmeden gerçek model yanıt veriyormuş gibi animasyon zamanlaması icat edilmez. `native_stream` profile geçişi, Speech'in cached token generation ve codec streaming sözleşmeleri tamamlandıktan sonra mümkündür.

### 11.1 V1 Batch vertical slice

1. Mikrofonu açıp 3–10 saniyelik tek Türkçe kullanıcı turunu yakala.
2. PCM verisinin gerçek sample rate ve kanal sayısını kaydet.
3. Speech codec'in giriş formatına açıkça resample et.
4. Kurulu checkpoint ve codec metadata uyumunu doğrula.
5. `build_dialogue_prompt(model, user_codes)` ve `generate(...)` ile turn-based üretim yap.
6. Empty EOS, bozuk output ve OOM durumlarını tipli hata olarak ayır.
7. Codec `decode` ile cevap WAV/PCM üret; Live playback ile seslendir.
8. `model_generation_completed`, `first_playable_audio`, `first_sample_output` anlarını farklı say.
9. UI'da yanıta ait gerçek süre, model ID, runtime profili ve hata varsa sebebi göster.
10. Kullanıcı `Stop` dediğinde playback kuyruğunu sustur; cancellation durumu ayrı raporlansın.

Mevcut Speech script'i `scripts/infer_audio.py` bir referanstır; Live'ın production SDK'sı değildir. Dosya I/O ile ilk dikey dilim doğrulanabilir, ancak sonraki aşamada dosyaya yazmadan binary IPC/PCM üzerinden çalışmak tercih edilir.

## 12. Speech sidecar ve süreç sahipliği

Python inference kodunu Electron renderer içinde çalıştırmaya kalkışma. Ağırlıklar, tokenizer/codec state'i ve GPU context'i ayrı Python sidecar process'inde bulunmalı. Electron **main process** sidecar'ı başlatır, izinli argümanları verir, sağlık durumunu izler, port/pipe ve kimlik doğrulamasını yönetir. Preload renderer'a yalnız dar bir türlenmiş köprü açar. Renderer asla `child_process`, `fs`, doğrudan Python subprocess ya da unrestricted local HTTP fetch yetkisi almaz.

Sidecar süreç özellikleri: `starting`, `handshaking`, `loading_model`, `ready`, `degraded`, `failed`, `stopping`, `stopped`. Bir sidecar `ready` olayını yalnız çekirdek API ve seçilen runtime yetenekleri doğrulandıktan sonra verir. Düzensiz process exit, crash, GPU OOM, incompatible checkpoint ve port conflict farklı hata kodlarıyla raporlanır.

### 12.1 Birinci açılış

İlk açılışta desteklenen OS, mikrofon izinleri, ses cihazları, CPU/GPU kullanılabilirliği, disk boşluğu, runtime ve seçilen model release'inin varlığı sorgulanır. İnternet yoksa kullanıcıya doğrudan "sistem çalışmaz" denmez; kurulu bir modelle offline devam seçeneği sunulabilir. Model kurulu değilse açık model kurulum ekranı gösterilir. Codec gerekliyse dependency indirme boyutu, lisans ve model kaynağı şeffaf biçimde sunulur.

### 12.2 Kapatma sırası

Kapanış: UI yeni tur kabul etmeyi bırakır → playback susturulur → varsa aktif generation cancel edilir → session state kapatılır → worker ve audio callback sonlandırılır → model/codec referansları bırakılır → sidecar'a kontrollü shutdown gönderilir → timeout sonrası process tree güvenle sonlandırılır → ayarlar atomik kaydedilir. Kapanış sırasında aktif IPC buffer'ının sonsuza kadar beklenmesi veya Renderer'ın yanıt vermez hâle gelmesi hata sayılır.

### 12.3 Otomatik yeniden başlatma sınırı

Sidecar arka arkaya çöküyorsa sınırsız restart döngüsü yapılamaz. Sınırlı exponential backoff, son hata ve model rollback önerisi kullanılabilir. Çökmeye neden olan model release'i yeniden seçilip sessizce tekrar tekrar yüklenmemelidir.

## 13. Model release seçme, kurma ve etkinleştirme

Live modelin sahibi değil, **Forge Registry tarafından yayımlanan artifact'in doğrulanmış tüketicisidir**. Gelecekteki registry implementasyonu `kaiwen.model.release` kanonik manifest sözleşmesini sunacaktır. Dosyaların hash'leri, codec kimliği, sample rate, codebook sayısı/büyüklüğü, acoustic-delay semantiği, model konfigürasyonu, runtime yetenekleri, lisans izinleri ve hedef donanım profili birbirine tutarlı olmalıdır.

```text
Discover release metadata
    ↓
Verify source / trust root / rights / compatibility
    ↓
Download to staging directory
    ↓
Verify every hash and file size
    ↓
Load codec + Transformer in isolated runtime
    ↓
Run bounded smoke inference and warm-up
    ↓
Atomically activate new release pointer
    ↓
Keep previous verified release for rollback
```

`artifact_exists` ≠ `verified` ≠ `loaded` ≠ `activated` ≠ `audible_success`. Dosyayı indirmek veya checkpoint açmak modelin konuşabildiğini kanıtlamaz. Yeni sürüm yüklenemezse ve güvenli eski release varsa rollback yapılabilir; ancak kullanıcının izni ve mevcut oturumun durumuna saygı gösterilir. Aktivasyon oturum ortasında kontrolsüz weights/codec değişimi yapmaz.

### 13.1 Token/codec uyuşmazlığı

Mimi referansı `24 kHz / ~12,5 Hz / Q8 / K2048` profilindedir. Araştırma hedefindeki Kaiwen Codec'in `24 kHz / yaklaşık 50 Hz / Q4 / K1024` olması **bir tasarım hipotezidir**. Özellikle codec'in `name`, `revision`, `codebook order`, `vocab`, `frame_rate`, `sample_rate` ve semantik/akustik eğitim sözleşmesi doğrulanmalıdır. Yalnız iki tensörün shape'inin uyuşması yeterli değildir.

### 13.2 Desteklenmeyen quantization

Bir dosyanın `int4` diye adlandırılması, Windows üzerindeki her GPU'da 4-bit inference yapılabildiğini göstermez. Model loader ilgili backend, kernel, device ve gerçek bellek kullanımını doğrular. Desteklenmeyen precision transparan hata üretir; sessizce FP32'ye çıkıp 2 GB VRAM sınıfında OOM vermesine izin verilmez. Fallback kullanıldıysa kullanıcıya ve benchmark'a kaydedilir.

## 14. Barge-in: konuşmayı kesmenin doğru anlamı

Barge-in, modelin konuşması sırasında kullanıcının konuşmaya girerek mevcut yanıtı kesmesi anlamına gelir. Bu davranış kullanıcı deneyimi açısından kritik fakat yanıltıcı bir "Stop" butonu animasyonuna indirgenemez. Barge-in en az üç katmanla ilgilidir: duyulmakta olan sesi hızlıca susturmak, eski generation'ın yeni PCM üretmesini durdurmak ve sonraki kullanıcı turu için mikrofon girişini uygun şekilde kabul etmek.

**İptal semantiği ayrı tutulur:**

| Kullanıcı niyeti | İşlem | Kaynak sahibi | Garanti sınırı |
|---|---|---|---|
| Sadece sesi sustur | `stop_playback` | Live | Ses kuyruğu temizlenir; GPU işini mutlaka iptal etmez. |
| Yanıt üretimini durdur | `cancel_generation` | Speech | Yeni token üretimi iptal edilir; daha önce duyulmuş ses geri alınmaz. |
| Mikrofonu kapat | `stop_microphone` | Live | Capture kapanır; Agent işi veya önceden üretilmiş ses otomatik iptal olmayabilir. |
| Oturumu bitir | `close_session` | Live + Speech | Session-owned buffers/KV/cache temizlenir; kaynak sahipliği biter. |
| Agent görevini iptal et | `cancel_agent_job` | Agent adapter | Yalnız cancellation destekleyen işler durabilir; dış dünyada tamamlanmış aksiyon geri alınmış sayılmaz. |

Barge-in'in güvenli sırası: (1) kullanıcı girdisi VAD/UI ile güvenilir biçimde algılanır; (2) Live playback hemen susturur; (3) `session_epoch` artırılarak eski ses geçersiz ilan edilir; (4) Speech'e generation cancel iletilir; (5) yeni `turn_id` açılır; (6) mikrofon buffer'ına yankı kalıntısı taşıyan örnekler için açık politika uygulanır; (7) önceki epoch'a ait gecikmiş IPC paketleri reddedilir.

Örneğin yanıt `gen-41` için ilk iki parça zaten çalındıysa, `gen-41`'in ağ/IPC kuyruğunda kalan üçüncü parçası, yeni tur başladıktan sonra eski konuşmanın sonunu aniden oynatamamalıdır. Bu yüzden yalnız `queue.clear()` yeterli değildir; header'daki generation ve epoch kontrolü **playback kabul sınırında** yeniden yapılır.

### 14.1 Echo cancellation ve sahte kesme

Yankı giderme devrede değilken fiziksel hoparlörden çıkan ses mikrofonla tekrar yakalanabilir. İlk sürümde kulaklıkla test, push-to-talk veya bas-konuş akışı desteklemek, kusurlu otomatik barge-in'den daha dürüst bir ürün deneyimidir. Gerçek çift yönlü konuşma hedefiyle test edilirse false-positive/false-negative kesme oranları, algılama gecikmesi ve ses kaybı raporlanır. Bir eşik bazlı VAD'ın bu sorunu çözdüğü varsayılmaz.

## 15. Mikrofon, hoparlör ve ses cihazı yaşam döngüsü

### 15.1 İzin durumları

Mikrofon erişimi kullanıcıdan açıkça alınır. `permission_unknown`, `permission_prompt`, `permission_granted`, `permission_denied`, `device_unavailable`, `capturing`, `muted` ve `recovering` durumları UI ile backend arasında tutarlı olmalıdır. Windows OS ayarında kapalı mikrofon için sonsuz izin isteyen döngüye girilmez. Kullanıcıya gerekli uygulama/OS ayarı gösterilir. Bir mikrofon izni reddedilirse önceden alınmış sesler gizlice kullanılmaz.

### 15.2 Cihaz değişimi

USB kulaklık çıkarılırsa veya varsayılan ses çıkışı değişirse: capture/playback callback durumu güvenli sonlandırılır, cihaz listesi güncellenir, mümkünse yeni cihaz açılır, buffer resampling profili tekrar müzakere edilir, yeni cihazın latency'si kaydedilir. Cihaz değişimi aynı `session_id` altında gerçekleşebilir, fakat audio stream kimliği ve clock domain değişimi açıkça belirtilmelidir. Cihaz seçimi başarısız olursa kullanıcı sessizliğe mahkûm edilmez; uygun alternatif varsa önerilir.

### 15.3 Kayıt kalitesi ve ses seviyesi

Input level meter mikrofonun gerçek RMS/peak değerlerine dayanmalıdır. Ağır sinyal analizi callback'inde değil uygun analiz worker'ında yapılır. Clipping, sessiz giriş, sample-rate conversion hatası, bozuk kanal mapping ve çok düşük ses için anlaşılır diagnostics gösterilir. Otomatik gain control varsayılan olarak doğru kabul edilmez; kullanıcının konuşma doğallığı ve codec performansı üzerinde ölçülür.

### 15.4 Birden çok uygulama ve exclusive mode

Bazı sürücüler mikrofonu veya hoparlörü exclusive modda açabilir. Live V1 mümkünse shared mode ile başlar; exclusive mode ancak açık donanım yeteneği ve kullanıcı seçimi varsa uygulanır. İkinci uygulamanın ses aygıtını kapması durumunda kullanıcıya cihaz hatası ve retry gösterilir; UI `listening` pozisyonunda donup kalmaz.

## 16. Türkçe sesli etkileşim, konuşma doğallığı ve akış

Kaiwen Live'ın çekirdek ürünü Türkçedir. UI metinleri Türkçe öncelikli hazırlanır, teknik alanlar ve model kimlikleri gerektiğinde İngilizce kalabilir. Türkçe konuşma kalitesi yalnız kelimelerin anlaşılmasından ibaret değildir: sesin akıcılığı, doğal duraksama, vurgu, tonlama, karşılıklı tur geçişi, soru tonlaması, kısa geri bildirimler, ünlemler ve kullanıcı araya girdiğinde konuşma davranışı hedeflenir.

Önemli bir sınırlama: Bu özelliklerin hepsi UI'da etkinmiş gibi sunulamaz. Model eğitiminde bulunmayan backchannel, akustik overlap veya noktalama dışı prozodi davranışı yalnız animasyonla kazanılmaz. Speech modelinin gerçekten öğrendiği özellikler ve değerlendirilen ses çıktısı belirleyicidir.

### 16.1 Turn boundary politikasının gelişimi

- **V1 güvenilir mod:** Push-to-talk veya açık "Konuşmayı bitir" butonu. Hatalı VAD kararlarının teknik borç oluşturmasını azaltır.
- **V1.5 deneysel mod:** VAD eşik + sessizlik süresi + minimum konuşma süresi; kullanıcı açıkça otomatik tur sonunu etkinleştirir.
- **V2 araştırma:** Semantik/akustik end-of-turn tahmini, streaming state ve konuşma sırasında kısmi üretim. Yanlış erken bitirme ve gereksiz bekleme birlikte ölçülür.

Sadece sessizlik süresi kısa diye Türkçe cümleyi bitmiş saymak yanlış olabilir. Türkçede ekler ve cümle sonu anlamı önemlidir; agresif chunking modelin bağlamını kesebilir. VAD + semantik turn estimator birleşimi ileride ayrı deney konusu olacaktır.

### 16.2 Diğer diller ve tek model hedefi

İlk ürün yalnız Türkçe hedefler. UI'da bir dil menüsünün bulunması modelin çok dilli yeteneğini kanıtlamaz. İngilizce/multilingual otomatik geçişi, desteklenmeyen dillerde kusursuz konuşma veya modelin her aksanı tanıması vaat edilmez. Farklı Türkçe bölgesel aksan ve konuşma hızları test setinde ayrı dilim olarak ele alınır.

## 17. UI/UX: tek ekran, az adım, gerçek durum bilgisi

UI siyah–beyaz/gri ağırlıklı, temiz, ferah ve güçlü tipografili olmalıdır. React bileşenleri önce `kaiwen-design` paketinden seçilir. Animasyonlar yalnız akıcı durum geri bildirimi için kullanılır; sesin gecikmesini gizleyen rastgele bekleme hareketleri veya ekranı dolduran görsel parazitler kullanılmaz. Kullanıcı arayüzü çalışmayan model özelliklerini satış yüzeyi gibi göstermez.

### 17.1 Önerilen ekranlar

| Ekran | Kullanıcının görevi | Minimum davranış |
|---|---|---|
| `Home / Voice` | Konuşmayı başlat, durdur, dinle | Net mikrofon, durum ve playback kontrolü |
| `Model Library` | Kurulu modeli seç, doğrula | Model adı, sürümü, boyutu, codec, uyumluluk |
| `Devices` | Mikrofon/hoparlör seç ve test et | Device loopback ve input meter |
| `Settings` | Tema, dil, gizlilik, audio ayarları | Kaydet/geri al; validation |
| `Diagnostics` | Neden ses gelmiyor? | Sidecar, audio, GPU, sürüm ve son hata |
| `About` | Sürüm, kaynaklar, lisanslar | Açık kaynak/lisans ve release bilgileri |
| `Agent Tasks` | Opsiyonel görevi başlat/takip et | İnsan onayı ve ayrı iptal semantiği |

İlk sürümde hepsi ayrı sayfa olmak zorunda değil; `Home`, küçük `Settings`, `Model/Device` drawer ve basit diagnostics yetebilir. Karmaşık sidebar, çok sekmeli konuşma arşivi ve animasyon stüdyosu, başarılı ilk ses döngüsünden önce gerekli değildir.

### 17.2 Ekranın konuşma durumları

UI, gerçekte gerçekleşen olayları göstermelidir: `Model yükleniyor`, `Hazır`, `Mikrofon dinliyor`, `Konuşmayı algılıyor`, `Yanıt hazırlanıyor`, `Ses çalınıyor`, `Durduruldu`, `Hata`, `Model yeniden deneniyor`. Farklı durumlar yalnız renge veya dalga animasyonuna bağlı kalmamalı; metin, ikon ve erişilebilir durum bildirimi birlikte kullanılmalıdır.

### 17.3 Erişilebilirlik

Klavye ile mikrofon başlatma/durdurma, odak görünürlüğü, buton isimleri, ekran okuyucu etiketleri, azaltılmış hareket tercihi, kontrast ve Windows metin ölçekleme davranışları test edilir. Ses dışında kullanıcının başarısızlığa dair görsel/tekst geri bildirimi olur. Erişilebilirlik, ayrı bir future backlog kutusuna ertelenip tamamen unutulamaz.

### 17.4 Konuşma geçmişi ve transkript problemi

Speech-native pipeline otomatik transkript üretmeyebilir. Konuşma geçmişinde metin gösteriliyorsa `transcript_source` açık olmalıdır: `verified`, `asr_unverified`, `user_entered` veya `unavailable`. Uydurulmuş transkript veya eksik metin kullanıcı tarafından gerçekten söylenmiş gibi arşivlenmez. V1'de varsayılan olarak kalıcı ses geçmişi tutulmaz; kullanıcı sonradan açıkça kayıt özelliğini etkinleştirirse saklama, silme ve şifreleme politikası yazılır.

## 18. Gecikme sözlüğü: hissedilen hız nasıl ölçülür?

"Hızlı" sözcüğünün sayısal karşılığı yoksa performans çalışması tutarlı olamaz. Bu nedenle en az aşağıdaki timestamps tutulur:

- `capture_first_sample_ns`: Kullanıcının ilk PCM örneğinin cihazdan alındığı an.
- `turn_end_decided_ns`: Kullanıcı bitirdi veya güvenilir turn-end kararı verildiği an.
- `model_request_queued_ns`: Live sidecar'a geçerli generation isteği verdiği an.
- `model_first_token_ns`: Speech modelinin ilk anlamlı acoustic token üretimi.
- `first_playable_chunk_ns`: Buffer'ın decode edilen ve cihazda çalınabilecek ilk PCM parçasını aldığı an.
- `playback_first_sample_ns`: Çıkış cihazına ilk PCM örneği teslim edildiği an; fiziksel hoparlör akustiğine ilişkin ek gecikme ayrı olabilir.
- `generation_complete_ns`: Modelin bütün yanıtı ürettiği an.
- `playback_complete_ns`: İzinli yanıt sesinin tamamının cihaz kuyruğundan çalındığı an.

**TTFA tek metrik değildir.** Model açısından ilk token gecikmesi, decoder açısından ilk playable chunk ve kullanıcı açısından çıkış cihazına ilk PCM teslimi birbirine karıştırılmamalıdır. İmkân varsa cihaz loopback testiyle gerçek duyulan ses gecikmesi de ayrıca ölçülür.

### 18.1 RTF ve gerçek zamanlılık

`RTF = compute_seconds / produced_audio_duration_seconds`. Uzun bir 5 saniyelik ses için 2 saniye hesaplama, `RTF=0.4` verir; bu gerçek zamanlı üretim açısından uygun işaret olabilir, fakat ilk sesin 1,5 saniye geç gelmesini tek başına açıklamaz. TTFA ve RTF ayrı raporlanır. Sıfır gecikme hissi araştırma hedefidir; kanıtlanmış ürün özelliği değildir.

### 18.2 Pilot performans matrisi

| Profil | Ölçüm | Kabul şekli |
|---|---|---|
| Cold start | Model indirimsiz yükleme, disk okuma, warm-up | Test cihazı ve süre raporu |
| Warm turn | 2–5 saniyelik kullanıcı konuşması | p50/p95 ve hata sayısı |
| Long turn | 30–60 saniyelik ses girişi | Memory leak / timeout / UI kararlılığı |
| Repeated turns | En az 50 tur | Cumulative VRAM, leak, crash |
| Interrupt | İlk ses çalarken kesme | Eski generation sesinin geri gelmemesi |
| Device swap | USB çıkışı veya varsayılan cihaz değişimi | Recovery ve durum açıklığı |
| Slow device | CPU veya düşük performans GPU | Capability/fallback gerçekliği |
| Missing model | Release hiç yüklenmemiş | Hata ve yönlendirme, sahte Ready yok |
| Bad artifact | Model checksum uyuşmaz | Fail-closed ve rollback |

Örnek sayısı, warm/cold dağılımı, cihaz adı, GPU driver, precision, codec revision ve model hash kaydedilmeden iki benchmark "aynı koşullarda" kabul edilmez.

## 19. 2 GB VRAM hedefi ve donanım profilleri

Kaiwen Live'ın düşük VRAM cihazlarda çalışması ana araştırma hedeflerinden biridir. Burada **2 GB bir kalite sözü değil bir kaynak bütçesidir**. Transformer ağırlıkları, codec, KV cache, CUDA/PyTorch allocator, temporary tensors, quantization kernel, GPU display process, resampling ve concurrency birlikte değerlendirilir. 50M FP16 Transformer teorik ağırlıklarının yaklaşık 100 MB olması bütün uygulamanın 100 MB VRAM ile çalışacağı anlamına gelmez.

**Önerilen ölçüm profilleri:**

1. **Geliştirici referansı:** RTX 4050 6 GB VRAM üzerinde öncelikle correctness ve gerçek ses kalitesi doğrulaması.
2. **Hedef cihaz:** Yaklaşık 2 GB kullanılabilir VRAM koşuluna karşılık gelen kısıtlı GPU; gerçek cihaz veya güvenilir sınırlandırılmış koşul ile test.
3. **CPU fallback:** İnference çalışıyorsa gerçek hız ölçülür; kullanıcıya "realtime" etiketi otomatik verilmez.
4. **Aynı sistemde GPU yükü:** Tarayıcı, masaüstü compositor veya başka GPU process'i yük oluşturduğunda ölçüm.

### 19.1 Bellek ölçümünün parçalanması

Live şu değerleri ayrı kaydetmelidir: model ağırlıkları, codec ağırlıkları, peak allocated VRAM, peak reserved VRAM, process toplam VRAM, KV cache büyüklüğü, output queue bytes, OS/audio buffer ve CPU RSS. `torch.cuda.max_memory_allocated()` tek başına GPU toplamını göstermeyebilir; OS seviyesinde VRAM tüketimi ayrıca kontrol edilir.

### 19.2 OOM durumda güvenli davranış

OOM'dan sonra başarısız generation invalid edilir, çalınmamış ses release edilir, mümkünse runtime korunaklı biçimde toparlanır ve kullanıcıya anlaşılır hata sunulur. GPU tekrar tekrar OOM verirken aynı modeli otomatik yükleyen sonsuz döngü olmamalıdır. Desteklenen daha küçük/quantized sürüm varsa **yalnız doğrulanmış release** önerilebilir; doğrulanmamış modeli sessizce başka backend'de çalıştırmak olmaz.

## 20. Güvenlik ve gizlilik: ses verisi en hassas ürün girdisi

Live'ın elindeki mikrofon sesleri doğrudan kullanıcının özel alanına aittir. Bu sebeple default profil **ephemeral audio** olmalıdır. Mikrofon ancak kullanıcı açıkça etkinleştirdiğinde açılır; kapalı mikrofonu gizlice dinleyen "wake-word" modu V1 kapsamına sokulmaz. UI kapanıp izin iptal edildiğinde mikrofon callback'leri sonlanır. Yetki verilmiş olması sınırsız arka plan kayıt izni gibi yorumlanmaz.

### 20.1 Veri sınıflandırma

- **Geçici RAM sesi:** Sadece aktif session'ın input/output PCM buffers'ında bulunur; yaşam süresi sınırlıdır.
- **Teknik loglar:** Ses bytes, transkript, cihaz seri numarası, dosya yolları veya gizli kimlik bilgileri varsayılan log alanı değildir.
- **Hata raporu:** Kullanıcı ayrıca izin vermedikçe ses içeriği veya otomatik kaydedilmiş WAV gönderilmez.
- **İsteğe bağlı arşiv:** Ancak kullanıcı etkinleştirdiyse, açık saklama/silme kuralları ve güvenli storage ile.
- **Agent tool içeriği:** Session audio verisi Agent'a "varsayılan her tur" olarak aktarılmaz; ihtiyaç, yetki ve minimum veri ilkesi uygulanır.

### 20.2 Electron güvenliği

`contextIsolation: true`, `nodeIntegration: false`, mümkünse etkin ve test edilmiş sandbox, dar preload IPC allowlist, içerik güvenlik politikası, güvenli navigation handler ve dış URL kontrolü zorunlu kabul edilir. Renderer kaynaklı JSON her zaman güvensiz input'tur. `open_file`, `download_model`, `set_device`, `start_sidecar` gibi aksiyonlar uygulamanın izin verdiği kapsamdan çıkamaz. Model dosyaları symlink/path traversal ile başka kullanıcı dosyalarını overwrite edemez. Gerekirse lokal IPC için random secret + erişim kontrolü kullanılır; açık localhost service "nasıl olsa lokalde" denip internetteki sayfalara açık bırakılmaz.

### 20.3 Model tedarik zinciri

Manifest hash kontrolü dosyanın beklenen bytes ile eşleştiğini söyler; kaynağın güvenilir olduğunu **tek başına** kanıtlamaz. İmzalı release veya sabit trust root, güvenli model loader, codec bağımlılıkları ve izinli indirme adresleri değerlendirilmelidir. Keyfi Python pickle ile bilinmeyen checkpoint çalıştırılmaz. Speech'in mevcut `torch.load(weights_only=True)` yolu korunur ama gerekli diğer doğrulamalar atlanmaz.

### 20.4 Güncelleme güvenliği

Desktop installer güncellemeleri ile model release güncellemeleri birbirinden bağımsızdır. UI güncellemesi protokolünü yükseltiyorsa sidecar compatibility handshake ve migration planı bulunur. Model silme/güncelleme açık kullanıcı onayı ve atomik rollback ile gerçekleşir. Release indirme başarıyla başladı diye doğrulanmış kurulum sayılmaz.

## 21. Hata modeli ve recovery matrisi

Her hata en az `code`, `user_message`, `technical_detail`, `retryable`, `session_id`, `correlation_id` içerir; teknik stacktrace kullanıcıdan saklanıp geliştirici logunda gerekli ölçüde tutulabilir. Uydurulmuş başarılı sonuç gönderilmez.

| Hata | UI mesajının anlamı | Otomatik davranış | Kullanıcı eylemi |
|---|---|---|---|
| `MIC_PERMISSION_DENIED` | Mikrofon izni yok | Capture başlatılmaz | OS ayarına git, tekrar dene |
| `AUDIO_DEVICE_GONE` | Seçilen aygıt ayrıldı | Gerekirse stream durdur | Başka cihaz seç |
| `AUDIO_FORMAT_UNSUPPORTED` | Format eşleşmedi | Açık resample yolu test edilirse uygulanır | Cihaz/formatı değiştir |
| `MODEL_RELEASE_MISSING` | Kurulu model yok | Download otomatik başlatılmaz | Kaynak/lisansı incele, yükle |
| `MODEL_INCOMPATIBLE` | Codec/model uyumsuz | Inference reddedilir | Uyumluyu seç |
| `MODEL_HASH_MISMATCH` | Artifact bozuk | Quarantine/rollback | Yeniden doğrulanmış sürüm indir |
| `RUNTIME_HANDSHAKE_FAILED` | Sidecar sözleşmesi uyuşmuyor | Kısıtlı retry | Uygulama/runtime sürümünü kontrol et |
| `GPU_OUT_OF_MEMORY` | GPU belleği yetersiz | Generation iptali | Desteklenen küçük model/CPU profili |
| `GENERATION_EMPTY` | Model ses üretmedi | Sahte ses oluşturulmaz | Başka tur/model dene |
| `PLAYBACK_UNDERRUN` | Ses üretimi/aktarımı yetişmedi | Stale audio koruması sürer | Performans diagnostiklerini aç |
| `AGENT_NOT_CONFIGURED` | Agent yolu kapalı | Fast path etkilenmez | İsteğe bağlı Agent kur/etkinleştir |
| `NETWORK_NOT_REQUIRED` | Offline mod | Model zaten kuruluysa konuşma devam | Ağ bağlantısı gerekmez |

Bu kodlar **HEDEF taxonomy**'dir; çalışan hata enum'u değildir. Speech tarafındaki tipli hata sınıflarıyla map edilir ve kullanıcıya tek bir köklü `Unknown Error` yerine mümkünse çözüm üretir. Recovery başarısızsa session `failed` olur; UI bunu göstermeden `listening` durumuna geri dönemez.

## 22. Agent entegrasyonu ve metin yanıt sorunu

Kaiwen Live'ın ilk sürümünde Agent entegrasyonu şart değildir. Yerel Türkçe konuşma kanıtlanmadan web araması, hava durumu, takvim, kod yazma veya çok adımlı görevleri normal fast path'e karıştırmak yanlış mimari önceliktir. Kaiwen Agent ayrı repo olarak tool policy, onay mekanizması, retry ve izleme görevlerini üstlenir. Live yalnız niyet ve oturum köprüsüne sahiptir.

### 22.1 Bir Agent görevi nasıl başlar?

Güvenilir ilk yöntem **kullanıcının Agent moduna açıkça geçmesidir**. Daha sonra eğitilmiş intent/özel kontrol tokenlarıyla otomatik yönlendirme düşünülebilir. Modelin yalnız ses üreten sürümünün `AGENT_QUERY` semantiğini öğrendiği varsayılamaz. Agent etkin değilse kullanıcıya "bu özellik hazır değil" diyeceğiz; gerçekte araç çağrısı yapılmadığı hâlde "internette baktım" diye ses üretmeyeceğiz.

### 22.2 Metin → ses köprüsünün gerçek sınırı

Agent çoğunlukla **metin veya yapılandırılmış sonuç** döndürür. Speech'in bugünkü sesi kodlayan ve ses üreten Transformer'ı bu metni alıp doğal sesle ifade eden doğrulanmış bir conditioning API'si sunmaz. Dolayısıyla üç farklı yol açıkça ayrı değerlendirilir:

1. **Gelecek speech-text conditioning:** Speech bu yeteneğe açıkça eğitilir, SDK sözleşmesi ve kalite testleri hazır olur.
2. **Geçici TTS köprüsü:** Agent metni ayrı bir Türkçe TTS motoruyla seslendirilir. Bu yol "native speech output" değil, farklı bir **Agent response path** olarak etiketlenir.
3. **Metin tabanlı görünüm:** Seslendirme desteği yoksa Agent yanıtını görsel panelde göster, sahte bir PCM üretme.

İlk üretimde gereksiz metin modeli dependency'si yüklemeden speech-only hızlı yol çalışabilmelidir. Agent failure, audio session'ı çökertmemelidir. Kullanıcı Agent job'ını iptal ettiğinde dış sisteme zaten gönderilmiş veya tamamlanmış bir yan etki geri alınmış sayılmaz.

### 22.3 Güvenlik ve onay

Agent araç kullanımından önce hangi hesabın/uygulamanın kullanılacağı ve hangi veri erişiminin verildiği açık olmalıdır. Yan etkili görevler (`send_email`, dosya silme, satın alma, sistem değişikliği vb.) uygun policy ve gerektiğinde insan onayı olmadan çalışmaz. Ses kayıtları veya başka bir konuşmadaki özel bilgiler sessizce üçüncü tarafa aktarılmaz. Prompt injection ve güvensiz tool output, Agent katmanının sorumluluğudur; Live bu sınırı bypass eden "yardımcı" kısa yollar açmaz.

## 23. Model kurulumu ve ilk kullanıcı deneyimi

İlk açılışta uygulama şu sorulara somut cevap verir: Ses cihazım bulundu mu? Mikrofon iznim var mı? Çalışır Speech runtime kurulu mu? Hangi model mevcut? Codec uyumlu mu? Bu cihazda hangi çalışma modu gerçekten destekli? Modelin indirilmesi gerekiyor mu? İnternet bağlantısı hiç yoksa ne yapabilirim?

Bir kurulum sihirbazı dört kısa basamaktan fazla olmamalı: (1) Runtime health; (2) mikrofon/hoparlör testi; (3) model seçimi ve lisans/indirme; (4) kısa sesli demo. Kullanıcının istemediği model otomatik indirilmez. İndirme boyutu ve depolama konumu seçilebilir; eksik disk alanı indirmenin ortasında değil ön kontrolde mümkün olduğunca saptanır.

### 23.1 Model bulunmazsa

Live uygulaması model olmadan da açılabilmeli; `Model required` ekranı ve cihaz testi mümkün olmalıdır. İnternet yoksa "model kurulmadığı için şu an konuşma yapılamıyor" açıklaması doğru bir durumdur. Fake runtime yalnız geliştirici/diagnostic modunda görünmeli; üretimde gizli fallback olmamalıdır.

### 23.2 Model kısmen bozuksa

Hash'i tutmayan veya metadata'sı uyumsuz model için tek seçenek crash değildir. Quarantine, teknik açıklama, yeniden doğrulama ve varsa son verified release'e dönüş sağlanır. Dosyaların varlığına bakıp loaded state gösterilmez. Kullanıcının seçili model tercihi bozuk dosya yüzünden geri döndürülemez biçimde kaybolmaz.

## 24. Telemetri, hata raporu ve gizlilik dengesi

Yerel yapılandırılmış telemetri, audio içerikleri depolanmadan performansı anlamayı mümkün kılar. Kullanıcı verileri varsayılan olarak uzak sunucuya yollanmaz. Diagnostics ekranı şu alanları gösterebilir:

```json
{
  "schema_version": "1.0.0",
  "session_id": "session-0001",
  "runtime_mode": "batch_turn",
  "model_release_id": "demo-unreleased",
  "device_profile": {
    "accelerator": "cuda",
    "gpu_name": "EXAMPLE GPU — NOT MEASURED",
    "precision": "fp16"
  },
  "measurement": {
    "ttfa_model_ms": null,
    "first_playable_audio_ms": null,
    "first_output_sample_ms": null,
    "rtf": null,
    "peak_vram_mb": null,
    "playback_underruns": 0
  },
  "notes": ["Unmeasured metrics must stay null; this example is a schema fixture."]
}
```

`null` değerler **ölçülmedi** anlamındadır; kullanıcıya `0 ms` diye sunulamaz. Loglarda model SHA/release ID gibi teknik referans tutulabilir ancak tam kullanıcı konuşması, kişisel kimlik bilgileri, ham PCM ve tahmini transcript varsayılan kayda girmez. Kullanıcı diagnostics dosyasını export etmeden önce hassas veri taraması ve onay akışı olmalıdır.

### 24.1 Test verisi ve fake mode raporu

Fake runtime'la ölçülen IPC ve UI gecikmesi, gerçek model latency'siyle aynı dashboard metriğine otomatik karıştırılmaz. Benchmark kaydı `runtime_mode`, `audio_source`, `model_release_id`, `real_inference` ve cihaz bilgisiyle etiketlenir. Gerçek model olmadan `0.2 RTF` gibi görünür bir başarı kaydı oluşturulmaz.

## 25. Uygulama konfigürasyonu ve kalıcı ayarlar

**HEDEF config örneği — bu dosyayı okuyacak gerçek loader henüz yok:**

```yaml
config_version: "1.0.0"
locale: tr-TR
theme: system
runtime:
  mode: batch_turn  # fake | batch_turn | native_stream
  device_preference: auto
  model_release_id: null
  allow_automatic_download: false
  allow_remote_inference: false
audio:
  input_device_id: default
  output_device_id: default
  capture_format:
    sample_rate_hz: 48000
    channels: 1
  transport_format:
    sample_rate_hz: 24000
    channels: 1
    sample_type: pcm_s16le
  turn_detection:
    mode: manual  # manual | vad_experimental
  playback:
    target_buffer_ms: 120
privacy:
  record_sessions: false
  send_diagnostics: false
agent:
  enabled: false
  require_confirmation_for_side_effects: true
```

Bu YAML'deki `capture_format.sample_rate_hz=48000` donanım için **öneri/örnek** değeridir; desteklenmeyen cihazı açmak için zorlanmaz. `target_buffer_ms=120` da benchmark kararı olmadan universal optimum değildir. Config dosyası yalnız kullanıcı ayarlarını tutar; local auth token, API key veya erişim bilgileri güvenli OS storage'a ayrılır. Sürüm yükseltmesi şema migration'ı gerektirir; eski config kaybına neden olmamalıdır.

## 26. Geliştirme, kurulum ve çalıştırma rehberi

### 26.1 Bugün gerçekten kullanılabilen referans komutlar

`kaiwen-live` reposunda henüz uygulama build komutları bulunmaz. Aşağıdaki örnek, **ayrı `kaiwen-speech` repository'sinin** mevcut kodunu temel alır ve Speech kaynak dizininde çalıştırılmalıdır:

```bash
# Kaiwen Speech repo içinde, gerçek baseline koduyla ilgili komutlar:
uv sync --frozen --extra dev
uv run ruff check .
uv run pyright
uv run pytest

# Mevcut benchmark yalnız single full-forward ölçümüdür:
uv run python scripts/benchmark.py --config configs/baseline_30m.yaml --frames 128

# Sesli inference için ayrıca gerçek checkpoint, audio extras ve input WAV gerekir:
uv sync --frozen --extra dev --extra audio
uv run python scripts/infer_audio.py samples/turkish.wav \
  --checkpoint artifacts/checkpoints/YOUR_REAL_CHECKPOINT.pt \
  --output artifacts/live-smoke/response.wav
```

**Koşullar:** `samples/turkish.wav` ve checkpoint path yalnız örnek olarak verilmiştir, repo üzerinde bunların bulunduğu garanti edilmez. `MimiCodec.from_pretrained` ilk çağrıda internet üzerinden model indirebilir. `benchmark.py` tek forward hesaplamasını ölçer; gerçek Live TTFA, RTF veya uzun oturum stabilitesi ölçmez. Yukarıdaki komutları bu README yazıldığı sırada çalıştırmış olduğumuzu iddia etmiyoruz.

### 26.2 Hedef Live komutları — henüz implementasyon yok

```bash
# HEDEF / NOT IMPLEMENTED — live repo uygulaması yazılınca önerilen yüzey:
pnpm install
pnpm dev:desktop
pnpm dev:sidecar
pnpm test
pnpm build:desktop

# Hedef Python sidecar projesinde kurulacak ayrı komut yüzeyi:
uv sync --extra dev
uv run pytest
```

Bu komutlar **gerçek `package.json`, `pnpm-lock.yaml`, `pyproject.toml`, testler ve build scriptleri eklendiğinde** yeniden doğrulanıp README'nin çalışma talimatına dönüştürülecektir. Repo iskeleti olmadan `pnpm install` tavsiye edilen bir başarı adımı sayılamaz.

### 26.3 Önerilen geliştirme akışı

İlk geliştirici `README`, workspace integration, Speech API/STREAMING ve Engineering Standards belgelerini okur; ardından çalışan dar prototip için yalnız masaüstü shell, ses loopback ve fake sidecar dikey dilimi geliştirir. Çoklu model registry ve Agent araştırması aynı PR'a yığılmaz. Her PR amacı, test kanıtı, kullanıcıya görünen davranış ve rollback adımı içerir.

## 27. Test stratejisi ve kalite kapıları

Testler dört katmanda düzenlenir: hızlı unit test, IPC/protocol contract test, gerçek ses ve model integration testleri, paketlenmiş Windows E2E testi. Sahte fixture testleri gerçek donanım testinin yerine geçmez. Bir test sadece modülün import edildiğini doğruluyorsa "ses geliyor" kanıtı değildir.

### 27.1 Unit test konuları

1. Session durum geçişleri; geçersiz `closed → listening` reddi.
2. Aynı turn için yeniden denemede `generation_id` yenilenmesi.
3. `session_epoch` değişince stale output reddi.
4. PCM chunk sample count/byte length tutarlılığı.
5. Sample rate ve kanal sayısı doğrulaması.
6. Bounded queue taşması ve drop metriği.
7. `stop_playback` ile `cancel_generation` ayrımı.
8. `stop_microphone` çağrısından sonra callback durması.
9. IPC event parse ve schema-version kontrolü.
10. Teknik event'ten UI durumuna deterministik dönüşüm.
11. Settings migration ve invalid config'in reddi.
12. Hata kodu → kullanıcı mesajı eşleme.

### 27.2 Contract test konuları

13. Live ↔ Speech handshake ve yetenek müzakeresi.
14. Batch-only modelin streaming olarak etiketlenememesi.
15. Model release manifest + audio token uyumluluğu.
16. Forge registry release hash zinciri ve load öncesi doğrulama.
17. İptal edilen generation'ın sonradan gelen audio chunk'ının atılması.
18. Binary header ve JSON control event schema eşleşmesi.
19. İki farklı protocol major sürümünün fail-closed davranışı.
20. Agent devre dışıyken speech-only yoldan normal yanıt.
21. Agent metin yanıtının doğrulanmış TTS bridge olmadan voice diye sunulmaması.
22. Device clock/sample index eşleşmesi ve stream reset.

### 27.3 Integration ve cihaz testleri

23. Gerçek mikrofon → playback loopback ve kulağa duyulan sonuç.
24. Gerçek checkpoint + doğru Mimi codec ile WAV giriş ve çıktı.
25. Sesli yanıt erken EOS üretirse doğru hata ve toparlanma.
26. Mikrofon izni reddedilince kayıt yapılmaması.
27. Ses giriş cihazı çıkarılıp takıldığında kurtarma.
28. Hoparlör çıkış cihazı değiştirildiğinde eski buffer'ın yanlış cihazda çalmaması.
29. 50 ardışık turda memory leak ve yüzdelik latency.
30. OOM/sidecar crash sonrası kullanıcı mesajı ve sınırlı retry.
31. Offline açılış ve offline inference (model önceden kuruluysa).
32. Bozuk/missing release için installer/rollback.
33. Windows packaged backend'in gerçekten başlaması ve kapanması.
34. Electron sandbox ve IPC allowlist güvenlik testleri.
35. CPU fallback için gecikme ve capability etiketlerinin doğruluğu.
36. Uygulama update ve model update sürüm uyumluluğu.

### 27.4 Gözden geçirilmesi gereken insan testleri

Türkçe anlaşılırlık, doğal duraksama, kullanıcıya erken cevap verme, yanlış kesme, sessiz mikrofondan yanıt gelmeme, farklı aksanlar ve yüksek arka plan gürültüsü gibi senaryolar gerçek dinleme değerlendirmesine eklenir. Duygu veya nezaket gibi öznel kriterler tek bir otomatik loss puanıyla temsil edilemez. Hangi sesi hangi modelin ürettiğini gizleyen kör A/B dinleme testleri, model karşılaştırmalarında tercih edilir.

## 28. Windows build, paketleme, yayınlama ve geri alma

V1 dağıtım yolu Windows üzerinde tek installer olabilir; fakat Electron dosyaları ile Python sidecar'ın binary bağımlılıkları birlikte paketlenmelidir. Model ağırlıklarının installer içine gömülmesi **otomatik varsayım değildir**: Boyut, lisans, sürüm güncellemeleri ve ilk offline deneyim için ayrı karar alınır. Büyük modelleri installer'ın yanında sürümlü ve imzalı/verify edilmiş indirme kanalı üzerinden yönetmek mantıklı olabilir.

**CI kalite kapıları:** TypeScript typecheck, ESLint, frontend build, Python lint/typecheck/test, protocol schema test, fake runtime E2E, Windows sidecar boot smoke, installer build, release checksum, security scan ve mümkünse donanım self-hosted benchmark. GPU gerektiren testler GitHub standart runner'da çalışıyor gibi gösterilmez; ayrı profile'da doğrulanır.

### 28.1 Release değişiklik kontrol listesi

- UI/frontend package version ile Electron release version tutarlı.
- Python sidecar runtime ve public protocol major uyumlu.
- Kaiwen Speech package/import sürümü açıkça pinlenmiş.
- Model registry manifest sürümü destekleniyor.
- Release artifact'leri hash ve uygun imza yöntemleriyle korunmuş.
- Windows installer temiz sistemde açılıp kapatılabiliyor.
- Audio cihaz izni, sidecar health ve model bulunmama durumları gösteriliyor.
- Previous release rollback veya düzeltme planı kayıtlı.
- Lisans bildirimleri, third-party attribution ve dağıtım izinleri kontrol edilmiş.
- Gizli token/kişisel veri installer veya CI artifact'ine sızmamış.

Windows code signing ve tam SmartScreen itibarı ilk günden otomatik elde edilir gibi davranılmamalıdır. Test edilmemiş release'i "production ready" diye yayımlamak yerine `experimental` veya `pilot` kanalı tercih edilir.

## 29. Performans/kalite dengesi ve araştırma deneyleri

İlk başarı metriği yalnız hız değil, **anlaşılır Türkçe konuşma + doğru tur davranışı + makul kaynak kullanımı** birleşimidir. Codec frame rate'inin 12,5 Hz'den 50 Hz'e yükselmesi, aynı konuşma süresi için temporal adım sayısını artırabilir; daha yüksek frame rate doğrudan daha iyi konuşma zekâsı ya da daha düşük latency garanti etmez. Model mimarisi, token hedefi ve codec reconstruction kalitesiyle birlikte değerlendirilmelidir.

| Deney | Kontrol | İncelenecek sonuç |
|---|---|---|
| Batch vs native stream | Aynı model + codec release | TTFA, output sürekliliği, parity |
| 20/40/80 ms capture chunk | Sabit cihaz ve model | CPU overhead, queue delay, VAD kararları |
| 100/200/300 ms playback buffer | Sabit gerçek output akışı | Underrun, duyulan gecikme |
| FP16 vs INT8 | Aynı veri ve release varyantı | Kalite farkı, VRAM, RTF |
| CPU vs GPU | Aynı tur veri seti | Cihaz bağımlılığı ve gecikme |
| Manual end vs VAD | Eşlenmiş Türkçe kayıtlar | Yanlış kesme, gereksiz bekleme |
| With/without echo suppression | Kulaklık ve hoparlör ortamı | Yanlış barge-in, ses kalitesi |
| Cold vs warm model | Aynı kurulu artifact | Başlangıç süresi, peak memory |

Başka model ve codec profillerinin karşılaştırılması, özellikle token CE/PPL gibi doğrudan karşılaştırılamayan metrikler için Forge Evaluation sözleşmesiyle yürütülür. Live, kullanıcı tarafındaki gerçek ses I/O metriğini üretir; Forge deney ve rapor yönetimini yapar. İki repo aynı benchmark sonucunu farklı isimlerle saklamaz.

## 30. Modüler API yüzeyi ve tasarım örnekleri

Aşağıdaki TypeScript kodu **HEDEF ARAYÜZ TASLAĞI**'dır, gerçek dosya değildir. Amaç Electron preload ile renderer arasında güvenli, dar ve test edilebilir işlemler göstermektir:

```ts
// HEDEF PSEUDOCODE — apps/desktop/src/contracts/live-api.ts
export type RuntimeMode = "fake" | "batch_turn" | "native_stream";
export type SessionState =
  | "created" | "initializing" | "ready" | "listening"
  | "processing" | "speaking" | "closing" | "closed" | "failed";

export interface LiveRuntimeCapabilities {
  protocolVersion: string;
  runtimeMode: RuntimeMode;
  nativeStreaming: boolean;
  bargeIn: boolean;
  modelReleaseId: string | null;
}

export interface LiveDesktopAPI {
  getCapabilities(): Promise<LiveRuntimeCapabilities>;
  listAudioDevices(): Promise<Array<{ id: string; label: string; kind: "input" | "output" }>>;
  selectAudioDevices(inputId: string, outputId: string): Promise<void>;
  startSession(): Promise<{ sessionId: string; state: SessionState }>;
  finishTurn(sessionId: string): Promise<void>;
  stopPlayback(sessionId: string): Promise<void>;
  cancelGeneration(sessionId: string, generationId: string): Promise<void>;
  closeSession(sessionId: string): Promise<void>;
}
```

Preload yalnız izinli `LiveDesktopAPI` yöntemlerini `contextBridge` üzerinden expose eder; renderer'a `ipcRenderer` bütün namespace'i, `spawn`, raw filesystem veya serbest URL indirme yetkisi verilmez. Metotların UI tarafındaki çağrı sayısı ses callback sayısıyla aynı değildir; callback audio pipeline doğrudan Live main/native audio katmanına gider.

**Hedef Python sidecar adapter örneği:**

```python
# HEDEF PROTOCOL ÖRNEĞİ — bu sınıflar henüz projede yoktur.
from typing import Protocol

class AudioSession(Protocol):
    async def submit_pcm(self, pcm: bytes, *, start_sample: int) -> None: ...
    async def end_turn(self, turn_id: str) -> None: ...
    async def cancel_generation(self, generation_id: str) -> None: ...
    async def close(self) -> None: ...

class SpeechBackend(Protocol):
    def capabilities(self) -> dict[str, object]: ...
    async def open_session(self, session_id: str) -> AudioSession: ...
```

Bu `SpeechBackend` interfacenin consumer adapter tarafına ait olması, `kaiwen_voice` model paketinin içinde adının aynen bulunmasını gerektirmez. Gerçek `Speech` SDK hazır olana kadar mevcut `load_checkpoint` / `generate` gibi fonksiyonları saran izole bir batch adapter yazılır; model blocklarına dokunulmaz. Contract testleri sonra `native_stream` adapter ile aynı business lifecycle'ı doğrular.

## 31. Başlangıç kilometre taşları: LIVE0–LIVE12

Aşamalar teknoloji listesi değil, her biri ayrı doğrulanabilir dikey teslimdir. Bir milestone'un ön koşulu test edilmeden sonraki büyük özelliğe geçilmez.

| Aşama | Çıktı | Tamamlanma kanıtı |
|---|---|---|
| `LIVE0` | Repo altyapısı, ADR, lockfile, temel CI | Temiz Windows checkout, ilk build/test geçiyor |
| `LIVE1` | Electron shell + Design tabanlı temel ekran | Uygulama açılıp kapanıyor, IPC sınırı testli |
| `LIVE2` | OS mikrofon/hoparlör loopback | Kullanıcı sesi gerçek cihazdan duyuluyor |
| `LIVE3` | Fake sidecar + session state machine | En az 10 hata/iptal state testi geçiyor |
| `LIVE4` | Gerçek Speech batch adapter | Doğrulanmış model+Mimi ile sesli tek tur |
| `LIVE5` | Binary PCM IPC, bounded buffer | Uzun tur/queue/sequence/fault injection testi |
| `LIVE6` | Model library, manifests, verification | Hash bozuk model reddi ve rollback |
| `LIVE7` | Diagnostics, performance timestamps | Cold/warm TTFA ve memory raporu |
| `LIVE8` | Chunked output ve stop playback | Ses kesme, stale packet testi |
| `LIVE9` | Speech native streaming adapter | Cached model+codec parity kanıtı; hâlâ deneysel |
| `LIVE10` | Barge-in ve cihaz recovery | Echo, VAD, interrupt, hot-swap cihaz testleri |
| `LIVE11` | Windows installer, beta release | Paketli sidecar + temiz makine smoke |
| `LIVE12` | Opsiyonel Agent bridge | Onaylı tool path ve metin/ses fallback testi |

**Başlangıç için en önemli hedef `LIVE0 → LIVE4` aralığıdır.** Bu tamamlanmadan `LIVE9` için sırf mimari çizerek ürünün çalıştığı ilan edilmez. `LIVE6`, `LIVE7` ve `LIVE11` bazı parçalarda daha erken başlayabilir; ancak `LIVE4` gerçek ses yanıtını doğrulama kilometre taşıdır. `LIVE12`, konuşma modelini gereksiz Agent dependency'sine bağlamadan daha sonra yürütülür.

### 31.1 Her aşama için değişiklik raporu

Codex her PR sonunda şu kanıtları sunmalıdır: dokunulan dosyalar, yeni public API, test komutları ve exit code'ları, kritik ekran görüntüsü veya ses artefact'i (izinli test fixture), yeni disk/VRAM kullanımı, güvenlik etkisi, geriye uyumluluk ve rollback. "Tamamlandı" ifadesi yalnız kodun yazılması değil, ilgili kabul testlerinin gerçekten çalıştırılması anlamına gelir.

## 32. Kabul testleri: bir ilk uçtan uca konuşma ne zaman başarı sayılır?

Bir kullanıcı kontrollü pilotunda sesli yanıtın başarılı kabul edilmesi için şu işlemler birlikte tamamlanmalı:

1. Desktop uygulaması izole process olarak açılır ve doğru model durumunu gösterir.
2. Mikrofon ve hoparlör gerçek cihazlarla test edilmiştir; mikrofon izni kullanıcının kontrolündedir.
3. Speech sidecar `ready` bilgisini gerçekten yüklenmiş model ve doğru codec ile bildirir.
4. Türkçe konuşma girişi gerçek PCM olarak alınır; ses formatı ve kayıt süresi geçerlidir.
5. Kullanıcı turu açıkça tamamlar veya onaylanmış turn detector kararı verir.
6. Inference gerçek model checkpoint'i ile gerçekleştirilir, fake runtime değildir.
7. Çıkan ses gerçekten hoparlörden duyulur; boş EOS veya error sessizce başarıya çevrilmez.
8. `session_id`, `turn_id`, `generation_id`, `session_epoch` ve chunk sequence tutarlıdır.
9. Playback stop eski chunk'ları tekrar oynatmaz; sidecar exit UI crash'e neden olmaz.
10. Uygulama kapatılınca mikrofon ve process handle'ları serbest kalır.
11. En az bir gerçek donanım profilinde cold/warm gecikme ve peak memory raporu vardır.
12. Bu kanıtlar test fixture, log/ölçüm ve gerektiğinde kısa izinli demo kaydıyla yeniden üretilebilir.

**Bu kriterler sağlanmadan:** "sıfır gecikme", "2 GB VRAM tüm cihazlarda", "insan gibi konuşuyor", "full duplex hazır" ve "tüm Türkçe aksanları mükemmel" gibi iddialar reddedilir. Başarılı bir tek tur demo, genel amaçlı güvenilir asistan başarısıyla eşdeğer değildir.

## 33. Kapsam dışı işler ve öncelik disiplinimiz

V1'de telefon santrali, gelen/giden arama, ses toplama sosyal ağı, herkese açık voice chat servisi, multi-tenant hosting, hesap sistemi, sürekli açık bulut agent, büyük bilgi tabanı yönetimi veya sıfırdan yeni görsel UI kütüphanesi geliştirmiyoruz. Çoklu konuşmacı eşzamanlı anlayış, tam çift yönlü konuşma ve otomatik Agent routing araştırma alanı olarak tutulabilir fakat ilk demo blocker'ı yapılmaz.

Günlük kullanıcı için en değerli etkileşim, mikrofonun açık olup olmadığını bilmek; ne zaman konuşabileceğini anlamak; gerçekten sesli yanıt almak; gerektiğinde durdurmak ve uygulamayı güvenle kapatmaktır. Ürün bu beş davranışta zayıfken başka özellik eklemek öncelik hatasıdır.

## 34. Açık kararlar ve çözüm süreci

| Karar | Mevcut eğilim | Kanıt/karar anı |
|---|---|---|
| Mikrofon callback konumu | Windows native main-side tercih edilebilir | Loopback latency/permission benchmark |
| IPC transport | Named pipe veya authenticated loopback | Windows ACL, binary transport ve packaging testi |
| İlk runtime | Batch-turn + fake test backend | Speech mevcut API ve checkpoint smoke |
| Model indirme | Kullanıcı onaylı, verified release | Forge manifest/trust root testi |
| Output codec transport | Önce PCM16, gerekirse float32 | Ses kalitesi/CPU/latency benchmark |
| Otomatik VAD | Varsayılan manuel, sonra opsiyonel | Türkçe yanlış kesme testi |
| Agent cevap seslendirme | İlk sürüm text panel; sonra ayrı ses köprüsü | TTS/Speech conditioning kalite testi |
| Windows updater | İmzalı uygulama release kanalı | Temiz makine ve rollback testi |
| Her konuşmayı kaydetme | Varsayılan hayır | Kullanıcı onayı, gizlilik ve silme testi |
| 2 GB VRAM | Araştırma hedefi, ürün garantisi değil | Gerçek peak VRAM, RTF ve ses kalitesi ölçümü |

Kararların değişmesi mümkündür; ancak uyum sözleşmesini etkileyen değişikliklerde gerekçeyi ADR olarak kaydet, producer/consumer uyumluluk testlerini güncelle ve README'yi gerçekle hizala. Yalnız teknik modaya göre, uygulanmamış beş yeni altyapı daha eklenmez.

## 35. Dokümantasyon haritası ve değişiklik kuralı

**Bu repo için hazırlanan dokümanların planı:**

- `README.md` — Ürün konumu, bugünkü gerçek durum, V1 sınırı ve çalışır sisteme geçiş.
- `AGENTS.md` — Codex/ajanlar için değişiklik, test, güvenlik ve anti-regression kuralları. **Henüz ayrı dosya olarak oluşturulacak.**
- `docs/ARCHITECTURE.md` — Desktop/sidecar/audio thread/IPC/oturum mimarisinin en ayrıntılı sözleşmesi. **Henüz oluşturulacak.**
- `docs/DESIGN_AND_UX.md` — Ekran akışı, Design tüketimi, mikro etkileşim, erişilebilirlik. **Henüz oluşturulacak.**
- `docs/AGENT_INTEGRATION.md` — Agent routing, tool policy, task lifecycle, sesli yanıt sınırları. **Henüz oluşturulacak.**

**İlgili hazır belgeler:** [Workspace Overview](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/OVERVIEW.md), [Cross-Repository Integration](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/INTEGRATION.md), [Engineering Standards](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/ENGINEERING_STANDARDS.md), [Workspace Roadmap](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/ROADMAP.md), [Speech Streaming](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/STREAMING.md), [Speech API](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/API.md), [Speech Performance](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/PERFORMANCE.md), [Forge Model Registry](https://github.com/ImtheKaiwen/kaiwen-forge/blob/8bf2af3b925bc1478328b4a26fcba36af74480fb/docs/MODEL_REGISTRY.md), [Corpus Export Contract](https://github.com/ImtheKaiwen/kaiwen-corpus/blob/3416d57ce0815af0cb8357c6727cd4ba889bd46d/docs/EXPORT_CONTRACT.md).

Yapılandırma, public API, codec uyumluluğu, event enum veya model release şeması değiştiğinde bir belgede güncelleme yapmak yeterli değildir. Üretici sözleşmesi, tüketici adapter'ı, fixture ve test birlikte güncellenir. `README.md` ürün durumunu yansıtan **yaşayan belgedir**: bir özellik gerçekten uygulandığında statü tablosu kanıt referansıyla değiştirilir; uygulanmadıysa hedef olarak kalır.

## 36. Sonuç: ilk ürün, ilk ses ve ilk güvenilirlik testi

Kaiwen Live'ın önceliği **çalışan sesli konuşma**dır. İlk adım sağlam bir Windows masaüstü shell'i ve gerçek mikrofon/hoparlör loopback'tir. İkinci adım session protokolü ve güvenli sidecar'dır. Üçüncü adım mevcut Speech referans koduyla gerçek batch inference'tır. Native streaming, akıllı kesme, kısıtlı VRAM, Agent ve çok daha doğal diyalog daha sonra ayrı ayrı testlerle geliştirilir.

Birinci demo şu soruya evet diyebilmelidir: **"Gerçek kullanıcı sesi gerçekten yerel Speech modeline girdi mi ve gerçek model yanıtı gerçekten hoparlörden duyuldu mu?"** Evet cevabından sonra sıra gelen mühendislik soruları gecikme, kalite, süreklilik, donanım erişilebilirliği ve hata kurtarmadır. Bu sırayı bozmayacağız.

---

**Dürüstlük notu (30 Ekim 2026):** Bu metin yeni `kaiwen-live` projesi için teknik gereksinim ve uygulama planıdır. Metnin kendisi çalışan Electron uygulaması, native streaming codec, 2 GB VRAM başarısı, Agent bağlantısı, paketli Windows build veya model release oluşturmaz. Bunların her biri bağımsız kod/test kanıtı gerektirir.
