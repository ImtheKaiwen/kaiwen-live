# Kaiwen Live — Teknik Mimari: Electron, Yerel Speech Runtime, Ses Akışı ve Oturum Yönetimi

> **Durum:** HEDEF MİMARİ / UYGULAMA ŞARTNAMESİ — çalışan uygulama veya benchmark raporu değildir.  
> **Belge:** `kaiwen-live/docs/ARCHITECTURE.md`  
> **Sahip:** Kaiwen Live; Speech'in model/codec algoritmalarını değiştirme yetkisi yoktur.  
> **Ana hedef:** Türkçe, yerel, speech-native, doğal ve düşük gecikmeli konuşma; ilk dikey dilimde tek kullanıcı, tek Windows cihazı, güvenilir turn-based gerçek ses.  
> **Temel kaynaklar:** [Live README](../README.md), [Live AGENTS](../AGENTS.md), [Workspace Integration](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/INTEGRATION.md), [Speech Streaming](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/STREAMING.md), [Speech API](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/API.md), [Forge Registry](https://github.com/ImtheKaiwen/kaiwen-forge/blob/8bf2af3b925bc1478328b4a26fcba36af74480fb/docs/MODEL_REGISTRY.md).

---

## 1. Belgenin yetkisi, kapsamı ve statü sözlüğü

Bu belge, Kaiwen Live'ın gelecekte yazılacak **uygulama mimarisini**, süreçler arası kontrol ve ses akışını, güvenlik sınırlarını, donanım yaşam döngüsünü, zamanlama ve senkronizasyon modelini ve başarının nasıl doğrulanacağını tanımlar. Ürün davranışına ilişkin kararlar [README](../README.md), Codex/ajan çalışma kuralları [AGENTS.md](../AGENTS.md), konuşma modelinin iç streaming sözleşmesi [Speech Streaming](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/STREAMING.md) içindedir. Burada amaç onları tekrar etmek değil, modülleri birbiriyle uyumlu **uygulanabilir interface ve durum makinelerine** bağlamaktır.

Belgede üç statü kullanılır:

- **MEVCUT / DOĞRULANMIŞ KOD:** `kaiwen-speech` reposunun bugün gerçekten içerdiği import, fonksiyon veya CLI. Bu ifadeler mevcut kaynak dosyalarına dayanır; uçtan uca kullanımın bu oturumda koşulduğu anlamına gelmez.
- **HEDEF / NOT IMPLEMENTED:** Kaiwen Live içinde henüz yazılmamış public interface, klasör, proses, IPC protokolü, native stream veya UI. Kod blokları spesifikasyon/fixture niteliğindedir.
- **DENEYSEL / KARAR GEREKİR:** Audio device backend'i, Python–Electron IPC transport'u, streaming chunk süresi, resampler ve model precision gibi profil/benchmark ile seçilecek alternatifler.

`kaiwen-live` GitHub deposunda 30 Ekim 2026 tarihinde yalnız başlangıç `README.md` bulunduğu kontrol edilmiştir. Yerel çalışma alanına eklediğimiz kapsamlı README ve AGENTS dosyaları teknik dokümantasyon taslaklarıdır; bunlar Electron uygulamasını oluşturmuş sayılmaz. Bu belge hazırlanırken Live backend'i, native audio runtime'ı, TTS/ASR zinciri veya canlı sesli demo **oluşturulmamıştır**. İlerleyen geliştirmelerdeki değişiklikler kod, test ve gerçek cihaz kanıtıyla ayrıca raporlanacaktır.

### 1.1 Değişmez ürün sözleşmesi

1. **Local-first:** V1 mikrofon sesi yalnız yetkili yerel süreçlerde akar; sessiz bulut STT, model API'si veya arka planda dosya yüklemesi yoktur.
2. **Speech-native tercih:** Gerçek yanıt yolu `audio → codec → Speech Transformer → codec → audio`; metin, gerekiyorsa yardımcı gösterim/etiket veya opsiyonel Agent köprüsüdür.
3. **Tek kullanıcı/tek session:** Başlangıçta aynı cihazda bir aktif oturum; çoklu oturum desteği kaynak bütçesi ve concurrency testleriyle ileride açılır.
4. **Açık yetenekler:** Sahte demo, batch inference, parçalı PCM taşıma ve gerçek incremental model üretimi birbirinden ayrılır.
5. **Kayıpsız teşhis:** Kuyruk taşması, model/capture hatası, erken EOS, playback underrun ve iptal gecikmesi metriklerde görünür.
6. **Kullanıcı kontrolü:** Mikrofon izni, konuşmanın kesilmesi, cihaz seçimi, uygulama kapatma ve veri saklama davranışı kullanıcıya anlaşılır biçimde sunulur.
7. **Ölçülmemiş vaat yok:** 2 GB VRAM ve sıfır gecikme hissi araştırma hedefleridir; garanti, gerçek donanım testinden sonra verilebilir.

### 1.2 V1 kapsamında olmayanlar

Telefon santrali, arama yapma, sosyal ağ, yaygın bulut ses sağlayıcısı, sürekli ortam dinleme, dağıtık inference, sesli kimlik doğrulama, aynı anda birden çok konuşmacıyı kesin ayırma ve sürekli öğrenme V1 kapsamına girmez. Kaiwen Agent bağlantısı ileriki aşamada opsiyonel ve yetki kontrollüdür. Kullanıcının sesini gizlice saklayan varsayılan davranış kabul edilmez.

## 2. Repo sınırları, sahibi belirli bileşenler ve bağımlılık yönü

| Repository | Sahip olduğu sözleşme | Live ile ilişki | Kesin sınır |
|---|---|---|---|
| `kaiwen-live` | OS mikrofon/hoparlör, UI, IPC transport, oturum, model seçimi, kullanıcı izinleri | Nihai masaüstü tüketici | Model eğitimi veya codec algoritması kopyalamaz. |
| `kaiwen-speech` | Codec, Transformer, inference, public Python SDK ve native streaming state | Sidecar tarafından çağrılır | Electron, OS mikrofonu veya React bilmez. |
| `kaiwen-forge` | Deney, evaluation, model registry ve release onayı | Sürüm/manifest sağlayıcısı | Live'ın playback queue'sunu yönetmez. |
| `kaiwen-corpus` | Dataset hazırlama ve export | Dolaylı; model eğitimi kaynağı | Kullanıcı sesini Live'dan otomatik toplamaz. |
| `kaiwen-design` | React UI component ve token'ları | UI bileşen sağlayıcısı | Model/PCM transport veya Electron security yönetmez. |
| `kaiwen-agent` | Tool calling, approvals, guardrail ve retrieval | Opsiyonel asenkron köprü | Mikrofon callback veya Speech KV cache sahibi değildir. |

Bu altı depo kardeş dizinlerdir, üstteki `kaiwen-ai` bir Git monorepo değildir. Cross-repo sürümler kendiliğinden aynı commit'e bağlanmaz. Live'ın public protokolünde `schema_version`, Speech SDK uyumluluk aralığı ve model release kimliği **açık** tutulur. Git submodule kullanılması varsayılmaz. Üretim bağımlılığı lockfile, version pin ve doğrulanmış paketleme yöntemiyle çözülür.

**Önemli adlandırma:** Speech GitHub reposunun adı `kaiwen-speech`, bugünkü Python import namespace'i `kaiwen_voice`, distribution adı `kaiwen-voice` sürüm `0.1.0`'dır. Live code generation sırasında `import kaiwen_speech` çalışıyormuş varsaymamalıdır. İleride API geçişi yapılırsa migration/alias ve import contract testleri gerekir.

## 3. Üst düzey sistem: kontrol düzlemi, ses düzlemi ve gözlem düzlemi

```text
┌──────────────────────────── KAIWEN LIVE DESKTOP ──────────────────────────┐
│ Electron Renderer: React/TypeScript + Kaiwen Design                      │
│  Conversation • Devices • Model Manager • Settings • Diagnostics         │
│            │ allowlisted, typed preload bridge                            │
│            ▼                                                              │
│ Electron Main / App Supervisor                                            │
│  OS permission • window lifetime • secure IPC • runtime process           │
│            │                      ▲                                       │
│            ├── control messages ──┤                                       │
│            └── binary PCM frames ─┤                                       │
│                                   ▼                                       │
│ Local Python Sidecar / Live Runtime Adapter                                │
│  Protocol validation • session actor • audio conversion • telemetry       │
│            │                                                              │
│            ▼                                                              │
│ Kaiwen Speech Python SDK (external dependency, pinned)                    │
│  Mimi baseline / KaiwenCodec (future) → Transformer → speech output       │
│            │                                                              │
│            └── generation-aware PCM → bounded output → Playback device    │
└───────────────────────────────────────────────────────────────────────────┘
          │ registry artifact (local verified bundle)
          ▼
 Kaiwen Forge model release; optional Agent bridge (explicit tool path)
```

Bu çizim **mantıksal topoloji**, seçilmiş tek fiziksel transport değildir. Native ses I/O'nun Electron main, native audio worker veya yan process içinde yer alması benchmark ve Windows packaging kararına bağlıdır. Kullanılan kütüphanenin gerçek-time callback garantileri ve izinleri onaylanmadan mikrofon yolunu otomatik renderer'a bağlamayız.

### 3.1 Üç düzlem niçin ayrı?

**Kontrol düzlemi:** kullanıcı eylemleri, oturum komutları, cihaz/format pazarlığı, model yükleme, iptal, kapatma. Küçük, sürümlü JSON mesajları için uygundur. Kaybı/retry'si ve idempotency semantiği belirlenir.

**Ses veri düzlemi:** çok sayıda sık PCM blokları veya şeffafça tanımlanmış codec frame'leri. Binary payload ve bounded queue kullanır; her mesajı büyük JSON/base64'e dönüştürmez. UI frame rate'i ses akışını bloke edemez.

**Gözlem düzlemi:** log, health, error, queue depth, TTFA, RTF, cihaz istatistikleri. Sampled/aggregate olarak akar, default olarak ham ses veya transkript saklamaz. Tam hata nedeninin güvenli raporlanmasını sağlar; gerçek zamanlı audio callback'inin içinde telemetry upload yapılmaz.

### 3.2 Nedensellik zinciri

Kullanıcının `record` düğmesine basması → OS izni ve cihaz açma sonucunun doğrulanması → `listening` durumu → gerçekte alınan PCM chunk'larının sıra ve sample bilgisiyle taşınması → sonlandırılmış input turn → Speech'in kabul ettiği input → başlatılmış generation → gerçek audio chunk → hoparlör queue/OS callback → `speaking`/`playback.completed`. Her önemli aşama aynı `correlation_id` bağlamını sürdürür. Arayüz, kullanıcı düğmeye bastı diye `listening` veya backend bir token üretti diye `speaking` durumunu ilan etmez.

## 4. Hedef kod organizasyonu ve modül sınırları

```text
kaiwen-live/
├── README.md
├── AGENTS.md
├── docs/
│   ├── ARCHITECTURE.md                # bu belge
│   ├── DESIGN_AND_UX.md              # mevcut tasarım belgesi; uygulama planlanıyor
│   ├── AGENT_INTEGRATION.md          # mevcut tasarım belgesi; Agent köprüsü planlanıyor
│   └── decisions/                    # yalnız gerçek ADR ihtiyacı doğarsa
├── apps/
│   ├── desktop/
│   │   ├── electron/
│   │   │   ├── main.ts
│   │   │   ├── preload.ts
│   │   │   ├── runtime-supervisor.ts
│   │   │   ├── device-service.ts
│   │   │   ├── protocol-gateway.ts
│   │   │   └── security/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── features/conversation/
│   │   │   ├── features/devices/
│   │   │   ├── features/models/
│   │   │   ├── features/settings/
│   │   │   ├── features/diagnostics/
│   │   │   ├── components/
│   │   │   └── state/
│   │   └── package.json
│   └── sidecar/
│       ├── pyproject.toml
│       ├── src/kaiwen_live_runtime/
│       │   ├── app.py
│       │   ├── protocol/
│       │   ├── transport/
│       │   ├── sessions/
│       │   ├── audio/
│       │   ├── adapters/speech.py
│       │   ├── adapters/fake.py
│       │   ├── models/
│       │   └── telemetry/
│       └── tests/
├── packages/contracts/
├── configs/runtime.example.yaml
├── tests/contract/
├── tests/e2e/
├── tests/fault_injection/
└── .github/workflows/
```

**HEDEF, mevcut depo ağacı değildir.** İlk PR'da bütün klasörleri dummy dosyalarla doldurmak yerine fake sidecar + typed handshake + tek oturum + test ile dar bir vertical slice kurulur. Benzer işleve sahip `SessionManager`, `ConversationManager` ve `AudioManager` nesneleri sırf soyutluk için çoğaltılmaz. Her modülün sorumluluğu, giriş/çıkış contract'ı ve sahibi belli olmalıdır.

### 4.1 Electron main process

Pencere açma/kapatma, izin politikası, güvenli renderer IPC, sidecar'ın başlatılması/sonlandırılması, kilitli yerel veriler, model dosyalarının güvenli seçimi ve Windows paketleme bilgisinin sahibidir. Main, audio waveform render etmez ve PyTorch inference yapmaz. Diskteki model manifesti ile UI'ın gösterdiği isim arasında tek doğrulanmış kaynak kullanılır.

### 4.2 Electron preload

İzin verilen birkaç isimli metodun dar köprüsüdür. Genel `ipcRenderer`, `require`, `fs`, shell çalıştırma veya arbitrary file path write yetkisi renderer'a sunulmaz. Her olay dinleyicisi unsubscribe döndürür; bileşen remount olduğunda sızıntı bırakmaz.

### 4.3 Renderer / React

Sadece görünüm, erişilebilir etkileşim ve kullanıcının anlayacağı oturum durumlarını gösterir. Backend command'larının başarılı olduğu yalnızca yanıt/ack ile yansıtılır; audio callback veya token queue renderer içinde tutulmaz. Görsel waveform aggregate telemetriden beslenir; ses örneklerinin her biri React state'e konulmaz.

### 4.4 Sidecar / Python

Güvenilir loopback/pipe kontrol noktası, protocol decoder, Speech SDK adapter, session actor, batch inference, ileride native stream facade, model release loader ve hardware metrics görevlerini üstlenir. Dosya erişimi ve GPU yetkisi sınırlandırılır. Sidecar, Renderer'dan gelen onaysız Python kodunu, shell komutunu veya açık dosya yolunu çalıştıran generic RPC sunmaz.

### 4.5 Audio device worker

Mikrofon ve hoparlör sürücüsüyle konuşan, gerçek zamanlı sınırlara sahip katmandır. İşlemin Electron main içinde mi yoksa ayrı native worker'da mı yer alacağı seçilen ses stack'i ve kanıtlanan thread modeli ile belirlenecektir. Callback, ses üretim modeli kullanmaz; çok küçük PCM bloklarını ring buffer'a yazar/okur.

## 5. Süreç topolojisi, sahiplik ve güven sınırları

**Önerilen ilk fiziksel topoloji:** tek Electron main/renderer, bir sidecar process ve ses I/O için sınırları bilinen tek controller. En fazla **bir aktif Speech inference generation**; aynı GPU'da eşzamanlı birden çok model kurulumuna başlanmaz. Model yüklenecekse sidecar'ın belleği ve hazır olma durumları supervisor tarafından izlenir.

Süreç sınırları:

- Renderer **güvenilmez UI girdi yüzeyi** kabul edilir: DOM/XSS ya da bir UI bug'ı işletim sistemi veya runtime üzerinde keyfi komut yetkisine dönüşmemelidir.
- Electron main dar yetkili broker'dır. Renderer'a `selectModel()` dönerken tam path yerine doğrulanmış release kimliği verebilir.
- Sidecar GPU ve checkpoint okuyabilir; yalnız iç kullanıcıya açık transport dinlemeli. Authentication olmayan açık `0.0.0.0` servis yasaktır.
- Model release verisi ve dışarıdan alınan manifest güvenilmez input'tur. Dosya hash'i, boyut, imza/güven kaynağı ve dizin/symlink sınırları doğrulanır.
- Agent plugin veya tool işi ayrı, asenkron ve açık onaylı yoldur; ses callback'inden internete erişim yoktur.

Windows'ta child process başlatılırken executable path installer'ın paketlediği konumdan kesin çözülür, kullanıcı girişi shell string'ine eklenmez. `spawn`/eşdeğeri shell kapalı, argüman dizisiyle çalışır. Parent kapandığında sidecar'ın orphan kalmadığı ölçülür. GUI görünmüyor ama arka planda mikrofon açık bırakıldıysa bu kritik ürün hatasıdır.

## 6. Runtime olgunluk profilleri ve capability gerçeği

| Runtime modu | Gerçek Speech inference | PCM chunk aktarımı | Artımlı model/codec | User-facing statü |
|---|---|---|---|---|
| `fake` | Yok | Test amacıyla olabilir | Yok | `Simülasyon` |
| `batch_turn` | Var; model+codec ağırlığı gerekir | Çıkışta olabilir | Yok | `Tur bazlı yerel model` |
| `chunked_playback` | Var veya fixture | Var | **Hayır** | `Parçalı ses oynatma` |
| `native_stream` | Var | Var | **Evet** | `Gerçek zamanlı model akışı` |

`chunked_playback`, önce tamamı üretilmiş WAV'i parçalara bölmekten ibaret olabilir; **native streaming değildir**. `native_stream`, Speech'in gerçek streaming encoder/decoder state ve Transformer KV cache/continuation arayüzlerini gerektirir. Şu an `kaiwen_voice.inference.generate` tüm prefix'i yeniden hesaplar; KV cache public API'si yoktur. Hız veya çalışma modunun UI'da görünmesini sırf pazarlama için abartmak yasaktır.

### 6.1 Capability handshake gerekliliği

Client ile sidecar ilk oturumdan önce: sürümlü protokol kesişimi, desteklenen PCM formatları, sample rate, max session, release id, `batch_inference`, `native_streaming`, `chunked_playback`, `barge_in_manual`, `barge_in_auto` ve `agent_bridge` bayraklarını karşılaştırır. `native_streaming=false` gelirse UI native streaming seçeneğini açmaz. Capability bilgisinin değeri model, release ve runtime profili değiştiğinde yeniden hesaplanır; sabit bir boolean varsayılmaz.

### 6.2 Verilen sözün ölçülmesi

Fake audio fixture ile oynatılan ses gerçek performans benchmark'ına katılmaz. Batch model gerçek ses üretiyorsa kalite testi yapılabilir ama en düşük TTFA hedefini tutturmuş kabul edilmez. Native stream çalışıyorsa da barge-in ve gerçek konuşmacı ayrımı otomatik olarak kanıtlanmış sayılmaz. **Özellik bazlı kanıt** oluşturulur: hangi versiyon, hangi cihaz, hangi dataset ve hangi ölçüm yöntemi kullanılmıştır?

## 7. İlk dikey dilim ve uygulama sırası

**Minimum gerçek ürün zinciri:** kullanıcı mikrofon izin verir → belirli süre ses yakalanır → `turn.finish` → sidecar gerçek PCM'yi alır → Speech'in geçerli checkpoint/codec'i ile batch inference → yeni PCM hoparlöre oynatılır → metrikler oluşturulur → iptal ve kapatma temiz çalışır. Bu aşamada eldeki modelin Türkçe kalitesi isteneni vermeyebilir; bu ses I/O zinciri başarı ölçüsünden ayrıdır.

Tavsiye edilen geliştirme sırası:

1. **Fake fixture runtime:** typed handshake, JSON control, binary audio fixture, one active session, cancellation unit tests.
2. **Gerçek cihaz zinciri:** izinler, iki yönlü PCM, ses çıktısı; model olmadan cihaz testleri.
3. **Gerçek batch model:** mevcut Speech SDK adapter; safe release ve warm/cold performance.
4. **Stale-output güvenliği:** epoch barrier, generation cancellation, underrun ve kill/restart testleri.
5. **Native streaming (Speech dependency):** codec state ve KV cache API hazır olduğunda dönüştür.
6. **Opsiyonel Agent:** yalnız açık capabilities ve uygun speech-output arayüzü varsa.

Her aşamada bir öncekinin regression suite'i geçer. Tek PR'da tüm ürünü bitirmek beklenmez. İlk aşamada production-ready installer ve otomatik Agent tool calling'in bulunmaması başarısızlık değildir; ancak yapılan şeyin adı doğru olmalıdır.

## 8. Ses I/O fonksiyonel sözleşmesi: biçim ve dönüşümler

Sesin dört ayrı biçimi bulunabilir: fiziksel capture sample rate, canonical transport rate, model codec input rate ve fiziksel playback rate. Başlangıç önerisi **24 kHz mono PCM16**, ama fiziksel cihazlar 48 kHz veya 44,1 kHz çalışabilir. Resampler seçimi sürücü/latency ve kalite testinden sonra yapılır.

| Alan | Hedef format ve anlam | Test |
|---|---|---|
| `sample_rate_hz` | `24000` gibi açık pozitif tamsayı | Taraflar anlaşmalı; tahmini değer değil. |
| `channels` | V1 transport mono `1` | Stereo'dan dönüşüm kontrollü; channel map belgeli. |
| `sample_format` | `pcm_s16le` veya açık `float32le` | Byte-order ve sample width eşleşir. |
| `sample_count` | Bu chunk'taki **kanal başına** sample sayısı | Byte length doğru olmalı. |
| `start_sample_index` | Stream'in sıfır noktasına göre sample zamanı | Kesinti/tekrar monotonic kontrolü. |
| `capture_monotonic_ns` | Capture clock domain'inde timestamp | Cross-process farkında doğrudan çıkarılmaz. |
| `turn_id` | Bir kullanıcı girişi ve karşılık yanıt | Yeniden deneme aynı turn id altında yeni generation olabilir. |
| `is_final` | O giriş/çıkış akışının son parçası | `end_of_turn` ile otomatik eşit değil. |

**PCM16 byte hesabı:** 24.000 sample/s × 1 kanal × 2 bayt = 48.000 bayt/s. 20 ms chunk = 480 sample, 960 payload bayt. 48 kHz fiziksel capture'dan 24 kHz canonical'a resampling yapılınca gerçek zaman aralığı korunur; sayı alanları yeni sample rate ile yeniden hesaplanır. Model codec frame rate'i (Mimi'de yaklaşık 12,5 frame/s) 20 ms capture chunk büyüklüğüyle özdeş değildir.

### 8.1 Audio transform sırası

`device read → channel mapping → [gerekliyse resample] → PCM format conversion → bounded capture ring → transport → model input`. Model çıkışında `codec decode → canonical PCM → [device resample/channel mapping] → bounded playback ring → device write` gerçekleşir. Gain, limiter veya echo suppression ekleniyorsa sürüm, durumu ve gecikmesi raporlanır. İki kez resample veya bilinmeyen loudness normalization kalite deneylerini bozabilir.

### 8.2 Clock domain ve duration

Audio duration PCM frame sayısından hesaplanır; `sample_count/sample_rate_hz`. Wall clock UTC audit/rapor içindir. Monotonic clock tek process içinde süre ölçmek için kullanılır; Electron ve Python farklı proseslerinin monotonic timestamp'leri senkronize edilmeden birbirinden çıkarılmaz. OS audio playback clock, Qt/WebAudio veya Python timer'ı ile aynı kabul edilmez.

### 8.3 Mute, pause ve privacy

UI `mute` konumundayken yalnız mikrofon stream'ini hiç oluşturmamak veya açık stream'in sample'larını hiç tüketmemek farklı semantiklere sahiptir; V1'de mikrofon kapatıldıysa gerçek OS device handle serbest bırakılmalıdır. Uygulama arka plana geçtiğinde otomatik dinleme politikasının kullanıcı tarafından açıkça seçilmesi gerekir. Varsayılan sessizce mikrofon açma davranışı yasaktır.

## 9. Gerçek zamanlı thread ve queue mimarisi

Ses I/O callback yolu, Electron UI event loop'u, Python asyncio control loop'u ve PyTorch GPU işi farklı yürütme kaynaklarıdır. Hepsi aynı mutex/queue üzerinde sırayla büyük iş yaparsa kullanıcı donuk UI, kesikli ses ve artan gecikme görür. İlk hedef sistemin bu sınırları açık tutmasıdır.

```text
Capture callback (~kısa blok)
  │ try_push, no disk/no model/no blocking
  ▼
Bounded capture ring (sample-index aware)
  │ transport worker, sequence and PCM headers
  ▼
Authenticated local IPC (binary payload)
  │ sidecar receiver/control actor
  ▼
Bounded inference ingress
  │ turn assembler / optional streaming encoder
  ▼
Speech inference worker (torch inference_mode, model state owner)
  │ decoded output PCM + generation barrier
  ▼
Bounded output transport
  │ playback device adapter / resampler
  ▼
Bounded playback jitter buffer
  │ short callback read, silence/underrun counter on empty
  ▼
Audio device

Renderer ⇄ throttled UI state/metrics (parallel, never on callback hot path)
```

### 9.1 Callback kuralları

Audio callback içinde JSON parse, filesystem, model inference, internet isteği, per-sample React update, ağır FFT, Python garbage collection tetikleme, sınırsız allocation, kilit için bekleme veya dışarıdan gelen network verisini decode etme yapılmaz. Mümkün olduğunda preallocated lock-free/single-producer single-consumer ring tercih edilir. Bu teknik garanti kullanılan audio backend'e göre test edilmelidir; `thread-safe` etiketi tek başına real-time guarantee değildir.

### 9.2 Queue'ların ayrı limiti ve sahipliği

| Queue | Üretici → Tüketici | Limit sınıfı | Dolunca davranış |
|---|---|---|---|
| Capture ring | OS callback → audio transport | Süre cinsinden (ms) | Bekleme yapma; açık drop/error ve discontinuity işaretle. |
| IPC send | audio transport → sidecar | Byte ve chunk limiti | Kısa backpressure; timeout; turn abort veya noncritical drop. |
| Turn assembler | sidecar → Speech | Turn süresi ve RAM limiti | Makul üst sınır; sessiz sınırsız WAV biriktirme yok. |
| Output pending | Speech → transport | Byte + time limiti | Current generation için bounded wait veya cancellation. |
| Playback ring | device feeder → callback | Süre cinsinden (ms) | Alt akış yetersizse ölçümlü underrun, policy ile sessizlik. |
| UI metrics | workers → renderer | Mesaj frekansı | En eski görsel metrik atılabilir; ses atılmaz. |

Limitlerin sabit değerleri profil deneyiyle belirlenir. Örneğin 100–300 ms playback buffer başlangıç hipotezidir, doğrulanmış hedef değildir; kapasitenin aynı zamanda 2 GB cihaz belleği, cihaz buffer size ve p95 jitter'la uyumlu olması gerekir.

### 9.3 Backpressure sınıflandırması

Input audio kaybı, çıktının yavaşlaması ve UI telemetry kaybı birbirinden ayrıdır. Sıradan bir queue full durumunda sessizce sample atmak veri bütünlüğünü bozacağı için output'ta zaten eski generation ise discard, aktif generation ise bounded wait/controlled fail uygulanır. Capture'da callback'i bloke etmemek önceliktir; sample drop olduğunda `discontinuity` event'i ile sayım kaydedilir. Hataları concealment ile gizlemek kabul testinin kanıtını geçersiz kılar.

### 9.4 Üç farklı darboğaz

CPU resampling/ASR değil, Speech-native codec dönüşümü ve model inferansı; audio device format conversion; renderer waveform rendering. Bunların her biri ayrı profillenmelidir. GPU boşken ses kesiliyorsa sebep IPC queue, output callback veya resampler olabilir. Bir forward'ın hızlı olması sistemin interaktif olduğu anlamına gelmez.

## 10. Sesin başlangıç/bitiş sınırları ve kullanıcı turu

V1, kullanıcı konuşma turunu açık düğmeyle veya push-to-talk bırakmasıyla kapatabilir. Bu güvenilir temel, sessizlik algılayıcısı hatalarından ayrıdır. Sonraki otomatik endpointing için VAD/gürültü/overlap ölçülür; gerçek Türkçe konuşmalarda “ee”, “hımm”, sessiz düşünme veya uzun duraklar tura son verildiği anlamına gelmeyebilir.

### 10.1 Turn assembly kuralları

- Capture `sequence` sırası doğrulanır, `start_sample_index` boşlukları ve tekrarlar kaydedilir.
- Aynı tur içinde format değişimi açık `format_change` anlaşması gerektirir; kesilen cihaz yeni stream kimliğiyle başlatılabilir.
- `turn.finish` alındığında input flusher codec'in gerektirdiği son sample/chunk bilgisini kapatır; EOS ile aynı anlama gelmez.
- İki kere gelen `turn.finish` idempotent kabul edilir veya ikinci istek typed `already_finished` döner; ikinci generation başlatmaz.
- Model input'u boşsa sessizce yanıt uydurmak yerine `empty_input` sonucu oluşur.
- Çok uzun turn varsa bounded-memory ve explicit maksimum süre uygulanır; kullanıcıya görünür gerekçe sunulur.

### 10.2 VAD ve half-duplex

Half-duplex başlangıçta insan–model tur çakışmasını azaltır. Ses geri besleme varsa model konuşurken mikrofonu kapatmak veya echo suppression kullanmak tercihi ürün ayarı ve cihaz profiline göre test edilir. VAD ses enerjisinden konuşma çıkarsayabilir ama kullanıcı niyetini veya kimlik ayrımını tek başına vermez. Auto barge-in daha sonra ayrı kabul testleriyle açılır.

### 10.3 Session açmadan kısa capture mümkün mü?

Hayır, kullanıcı ses verisi kaydedilmeden önce açık session, yetki ve format anlaşması gerekir. Uygulamanın ilk açılış ekranında ses wave animasyonu göstermek, gerçek mikrofon kaydını başlatmak için kullanıcı izni sayılmaz. Session `ready` olmadan mikrofon komutu verilirse izin kontrolü yapılır ve readiness beklenir veya açık hata dönülür.

## 11. Oturum yaşam döngüsü: tek yetkili state machine

Oturumun nihai gerçeği renderer'ın buton rengi değildir. `SessionActor`/eşdeğer runtime controller, `session_id` altında izinli state transition'larını yürütür ve versiyonlu state snapshot döndürür. UI, bu snapshot'ı işler. Audio device service ve sidecar actor kendi düşük seviye durumlarını bildirir; birden çok bağımsız boolean'ın kombinasyonundan rastgele üst seviye state uydurulmaz.

```text
created
   │ initialize(version, model_release, device_profile)
   ▼
initializing ── failure ──► failed
   │ verified model + IPC + audio preflight
   ▼
ready
   │ start_listening(OS permission granted; input stream alive)
   ▼
listening ── turn.finish ──► processing
   ▲                               │ first playable PCM, device accepted
   │                               ▼
   └──────── next_turn ◄──── speaking
                  ▲               │ final output drained + ack
                  └──── ready ◄───┘

Any active state ── close ──► closing ── resources released ──► closed
Any active state ── fatal fault ──► failed ── explicit close ──► closed
```

Bu şema okunabilir bir özet, **tam transition tablosu** şu şekildedir:

| Current | Command/trigger | Guard | Next | Hata davranışı |
|---|---|---|---|---|
| `created` | `initialize` | Protocol ve release adayları belli | `initializing` | Hatalı config → `failed`. |
| `initializing` | `runtime.ready` | Manifest, model ve IPC doğrulandı | `ready` | Timeout → `failed`. |
| `ready` | `listen.start` | OS izni ve capture açıldı | `listening` | İzin yok → `ready` + typed error. |
| `listening` | `turn.finish` | En az bir geçerli input sample | `processing` | Boş tur → `ready`/`listening` + empty-input. |
| `processing` | `audio.first_playable` | Generation/epoch geçerli, playback ready | `speaking` | Queue/full veya device fail → recover/failed. |
| `speaking` | `output.drained` | Aktif generation final ack ve queue boş | `ready` | Playback error → recoverable error. |
| `ready`/`speaking` | `listen.start` | Politika full/half duplex izinli | `listening` veya altstate | Eşzamanlılık açık değilse ret. |
| Any active | `session.close` | İdempotent | `closing` | Timeout'ta fail-safe cleanup. |
| `closing` | `resources.released` | Device, transport, state ve worker kapalı | `closed` | Kaynak sızıntısı log/diagnostic. |
| Any active | Fatal fault | Kapatma/barrier oluşturuldu | `failed` | Yeni session veya açık recovery. |

`closed` terminaldir; aynı id altında yeniden `listen.start` olmaz. `failed` durumundan otomatik sessiz geri dönüş yapılmaz; `recover` geçişi ancak nedeni, gerekli cleanup ve yeni `session_epoch` tanımlanmışsa mümkün olur. `speaking` state'i sesin gerçekten hoparlör çıkışında olduğu iddiasıyla eşleştirilecekse `playback.started` cihaz ölçümüne dayanır; sırf chunk decode edilmesi yetmez.

### 11.1 Session alt durumları

Üst seviye state, mikrofon/hoparlör/modelin tüm durumlarını tek satıra sıkıştırmak zorunda değildir. Ayrı alt durumlardan örnekler: `capture_state = idle|starting|capturing|stopping|stopped|failed`, `generation_state = idle|queued|running|cancel_requested|cancelled|completed|failed`, `playback_state = idle|priming|playing|stopping|drained|failed`. Kullanıcıya ayrı gösterilecek kısım UX kararıdır; bu alt state'ler sistem teşhisi için korunur.

### 11.2 Race condition kuralları

`initialize` ile `close` aynı anda gelirse close öncelikli ve idempotent olur. `turn.finish` ile `session.close` yarışında yeni generation kapanmış session'a başlayamaz. `model.switch` yalnız yeni session/uygun idle boundary'de gerçekleşir. Bir session'ın aynı turu için iki `start_generation` farklı attempt kimliğiyle kayıt altına alınmadıkça kabul edilmez.

### 11.3 Kalıcı durum değildir

`session_id` cihaz ve model belleğinde yaşayan geçici nesnedir. Uygulama yeniden açıldığında aynı id'yi otomatik restore etmek, açık mikrofonu yeniden açmak veya eski generation queue'sunu devam ettirmek yasaktır. Saklanabilir ayarlar (seçilmiş cihaz takma adı, son model ID, telemetri tercihi) ile canlı ses state'i ayrıdır.

## 12. Kimlik modeli: session, turn, generation, epoch, stream, sequence

**HEDEF control/audio ortak kimlik sözleşmesi:**

| Alan | Sahip/oluşturma | Yaşam süresi | Yanlış kullanım riski |
|---|---|---|---|
| `session_id` | Live session manager | Tek oturum | Yeni oturuma eskisini taşımak. |
| `session_epoch` | Session manager, iptal/reset bariyeri | Session içi monoton artan integer | Eski sesin yeni turda tekrar oynatılması. |
| `turn_id` | Turn controller | User utterance + assistant response | Retry ile aynı mesajı iki kez cevaplamak. |
| `generation_id` | Runtime attempt oluşturucu | Tek inference denemesi | İptal sonrası eski tokenları kabul etmek. |
| `stream_id` | Producer | Bir PCM/control akışı | Input/output sequence karıştırmak. |
| `sequence` | Producer, stream-local | Bir stream için artan sayı | Paketi tekrar oynatmak veya boşluğu kaçırmak. |
| `event_id` | Event producer | Tek olay | Retry sonucu çift etkinin oluşması. |
| `correlation_id` | Edge request/trace entry | Uçtan uca nedensellik zinciri | Logların sebep-sonuç ilişkisini kaybetmek. |

`session_epoch` iptal/yeniden başlatmada **aktif kabul bariyeri** görevi görür. `sequence` aynı stream içinde sıralıdır, farklı stream'ler için global sıralılık zorunlu değildir. `generation_id` aynı turda retry sırasında yenilenir. UUID/ULID veya başka kimlik biçimi ilk protocol ADR'ında belirlenir; test fixture ID'leri güvenlik token'ı değildir.

**ACK/IDEMPOTENCY:** Kontrollere benzersiz `command_id` eklenmesi önerilir. Komut tekrarında aynı state mutation ikinci defa uygulanmaz, ilk sonucun `accepted|rejected|completed` durumuna başvurulur. Özellikle `session.close`, `turn.finish`, `generation.cancel` için iki kere çalıştırma kaynak sızıntısı veya ikinci üretim başlatmamalıdır.

## 13. Wire protocol: sürümleme ve kontrol düzlemi

Ortak [Integration](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/INTEGRATION.md) adı `kaiwen.live.session`, önerilen başlangıç sürümü `1.0.0`'dır. **Henüz sahada çalışan protocol implementation yoktur.** Her iki uçtaki contract dosyası, onaylı tek schema'dan üretilir veya iki dilli fixture testleriyle eşleşir. Schema'ların TS ve Python'da bağımsız sürüklenmesine izin verilmez.

### 13.1 Mesaj envelope örneği — HEDEF, çalışmayan fixture

```json
{
  "protocol_name": "kaiwen.live.session",
  "protocol_version": "1.0.0",
  "event_id": "evt-0042",
  "event_type": "generation.started",
  "session_id": "session-example-1",
  "session_epoch": 0,
  "turn_id": "turn-example-1",
  "generation_id": "generation-example-1",
  "stream_id": "control-example-1",
  "sequence": 42,
  "correlation_id": "trace-example-1",
  "occurred_at_utc": "2026-10-30T12:00:00Z",
  "monotonic_ns": 123456789000,
  "payload": {
    "runtime_mode": "batch_turn",
    "model_release_id": "unreleased-fixture"
  }
}
```

Bu alanların tip/format kuralları: `protocol_version` SemVer major uyumsuzluğu kontrolünden geçer; UTC zaman ISO 8601'dir; monotonic timestamp yalnız üretildiği domain'in içindedir; payload boyutları ve event type enum allowlist'i zorunludur; unknown event güvenli biçimde `unsupported` hatası döndürür. JSON ile PCM taşıma yoktur; bu örnek kontrol düzlemidir.

### 13.2 Örnek handshake — HEDEF

```json
{
  "protocol_name": "kaiwen.live.session",
  "protocol_version": "1.0.0",
  "runtime_mode": "batch_turn",
  "model_release_id": "model-fixture-id",
  "capabilities": {
    "batch_inference": true,
    "chunked_playback": true,
    "native_streaming": false,
    "barge_in_manual": true,
    "barge_in_auto": false,
    "agent_bridge": false
  },
  "audio": {
    "input_formats": ["pcm_s16le"],
    "output_formats": ["pcm_s16le"],
    "sample_rates_hz": [24000],
    "max_sessions": 1
  }
}
```

Bu **örnek** sidecar implementasyonunun gerçekten bu yeteneklere sahip olduğunu kanıtlamaz. `batch_inference=true` ancak uyumlu ve eğitilmiş checkpoint başarıyla load edilirse gerçek bir runtime capability olarak ilan edilebilir; fake fixture'da `batch_inference=false` olmalıdır. `chunked_playback=true` bir output'u dilimleyebilme kabiliyetidir, incremental decoder kanıtı değildir.

### 13.3 Event yönü ve typed kontrol kataloğu

| Yön | Ad | Kabul koşulu | Başarı kaydı |
|---|---|---|---|
| UI → Main | `microphone.enable` | Görünür kullanıcı niyeti, OS izin testi | `device.capture_started` |
| UI → Main | `microphone.disable` | İdempotent | Device handle released |
| UI → Main | `turn.finish` | Aktif `turn_id` var | `turn.input_finalized` |
| Main → Sidecar | `session.open` | Handshake ve release doğrulandı | `session.ready` |
| Main → Sidecar | `generation.start` | Turn input complete | `generation.started` |
| Main → Sidecar | `generation.cancel` | Aktif generation | `generation.cancelled` |
| UI → Main | `playback.stop` | Her zaman idempotent | `playback.stopped` |
| Main → Sidecar | `session.close` | Açık session | `session.closed` |
| Sidecar → Main | `audio.chunk_ready` | Geçerli epoch/generation | Enqueue veya bounded reject |
| Main → UI | `playback.started` | Device playback gözlendi | Kullanıcıya playing state |
| Main → UI | `runtime.error` | Typed error alanları doğrulandı | Recovery veya failed state |

Event adları **öneridir**, son enum Speech API ve Live sözleşme testlerinde sabitlenir. GUI trigger event ile runtime acknowledgement ayrı tutulur. `playback.stop` tek başına GPU üretimini durdurmaz; gerekli ise aynı kullanıcı hareketi hem playback stop hem `generation.cancel` talep eder, her ikisinin sonucu ayrı izlenir.

### 13.4 Protokol migrasyonu

V1 major değişiminde old client + new sidecar, new client + old sidecar testleri çalıştırılır. İstemci yalnız desteklediği aralıkta negotiation yapar. Unsupported major sürümde mikrofonu açıp ses toplamaya başlanmaz. Optional yeni field ancak default ve consumer fallback belirlenmişse minor sürümle eklenebilir. Eski `event_type` string'ini sessizce yeni anlama bağlamak breaking change'dir.

## 14. Binary PCM taşıma sözleşmesi

**Kontrol JSON, ses binary.** Hedef binary header mantıksal alanları aşağıdaki gibidir; bu belge byte düzeyinde endianness/layout sabitlemez. İlk transport ADR'ında sabit binary layout, minimum/maximum header length, CRC/AEAD gereksinimi, channel encoding ve serialized fixture golden byte testleri hazırlanmalıdır.

| Mantıksal alan | Tip/işlev | Zorunluluk |
|---|---|---|
| `magic` | Frame ailesi seçimi | Zorunlu |
| `protocol_version` | Binary frame parser sürümü | Zorunlu |
| `session_id` | Oturum eşleme | Zorunlu |
| `session_epoch` | Stale barrier | Zorunlu |
| `turn_id` | İlişkili kullanıcı turu | Zorunlu |
| `generation_id` | Output'un üretim denemesi; input için uygun nullable/etiket | Tanımlı |
| `stream_id` | Girdi/çıktı akış tipi | Zorunlu |
| `sequence` | Akış-local monotonik numara | Zorunlu |
| `start_sample_index` | İlk sample'ın stream timebase'inde konumu | Zorunlu |
| `sample_count` | Kanal başına sample sayısı | Zorunlu |
| `sample_rate_hz` | Anlaşılmış PCM hızı | Zorunlu |
| `channels` | Anlaşılmış kanal sayısı | Zorunlu |
| `sample_format` | PCM16LE veya float32LE | Zorunlu |
| `payload_length_bytes` | Binary payload'ın byte uzunluğu | Zorunlu |
| `flags` | final, discontinuity vb. | Tanımlı |

`payload_length_bytes == sample_count * channels * bytes_per_sample` kuralı sıkıştırılmamış interleaved PCM için zorunludur. Header+payload en üst sınırına uymayan mesaj allocate edilmeden reddedilir. Negative/zero sample count, desteklenmeyen sample rate, bilinmeyen flag, byte overflow, NaN/Inf float32 ve tutarsız offset fixture'ları ile sınanır.

### 14.1 Mantıksal doğrulama örneği — HEDEF PSEUDOCODE

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class PcmHeader:
    sample_rate_hz: int
    channels: int
    sample_format: str
    sample_count: int
    payload_length_bytes: int
    sequence: int
    start_sample_index: int


def validate_pcm_payload(h: PcmHeader, payload: bytes) -> None:
    widths = {"pcm_s16le": 2, "float32le": 4}
    if h.sample_format not in widths:
        raise ValueError("unsupported sample format")
    if h.sample_rate_hz <= 0 or h.channels < 1 or h.sample_count < 1:
        raise ValueError("invalid PCM geometry")
    if h.sequence < 0 or h.start_sample_index < 0:
        raise ValueError("negative sequence or position")
    expected = h.sample_count * h.channels * widths[h.sample_format]
    if expected > 1_048_576 or h.payload_length_bytes != expected or len(payload) != expected:
        raise ValueError("payload length mismatch or cap exceeded")
```

Bu örnek yalnız geometriyi doğrular; **gerçek transport parser değildir**. Byte layout, identity, epoch, frame rate negotiation, payload contents, nonce, dedup, auth ve CRC kontrolü ayrıca yapılmalıdır. 1 MiB örnek güvenlik üst sınırıdır; gerçek limit profil ve schema ile konfigüre edilir. Bu kodu “hazır binary decoder” diye yorumlamak yanlıştır.

### 14.2 Gecikme ve copy budget

Capture callback'inde bir kez ring'e kopyalama; transport'ta minimum copy; sidecar model adaptöründe gerekli dtype dönüşümü. Bu istenen mantıksal hedeftir; kullanılmış ses kütüphanesinin memory ownership/API semantiği görülmeden zero-copy vaadi verilmez. Windows named pipe, loopback socket, shared memory alternatifleri için throughput, frame p95 ve process restart maliyeti ölçülür.

### 14.3 Network ve güvenlik

Loopback TCP/WebSocket seçilirse yalnız `127.0.0.1` veya IPv6 loopback kullanılır; uzak arabirim açık değildir. Localhost tek başına yetkilendirme değildir: yetkisiz local process'in mic PCM'sini okuması/komut göndermesini önlemek için kısa ömürlü per-instance token, origin check, process identity veya pipe ACL mekanizması gerekir. Token stdout/URL/query string/log'a yazılmaz. CORS her origin'e açık değildir.

## 15. Stale output bariyeri: iptalden sonra ses neden geri gelemez?

İptal UI düğmesinin callback'ini çağırmak değildir. Dağıtılmış bir race yaşanır: model hâlihazırda bir sonraki PCM parçasını üretiyor olabilir, transport kanalında eski byte'lar vardır, playback ring'inde eski parçalar bekleyebilir ve cihaz DMA buffer'ında zaten kuyruğa verilmiş sample'lar kalabilir.

### 15.1 Dört operasyonun semantiği

| Komut | Hangi şeyi durdurur? | Durdurmadığı şey |
|---|---|---|
| `playback.stop` | Aktif sesin yeni chunk'larının oynatılmasını ve playback kuyruğunu | Speech modelinin token üretimini kendiliğinden durdurmaz. |
| `generation.cancel` | Model/codec üretimini, cooperative cancellation ile | Cihaz tamponundaki daha önce gönderilmiş sesi garantili olarak temizlemez. |
| `microphone.disable` | Capture device handle ve yeni input'u | Aktif output/generation'ı otomatik olarak durdurmaz. |
| `session.close` | Session aktörünü, kaynaklarını ve bağlı işlerini | Uygulama içindeki diğer session veya bağımsız yetkili görevleri otomatik olarak değil. |

Bir **kes** kullanıcı eylemi hem playback stop hem generation cancel tetikleyebilir. Her ikisi ayrı command/ack ile izlenir. Session close bunları ve cleanup'ı sıralı olarak kapsar ama kullanıcı yalnız sesi susturmak istedi diye session kapatılmaz.

### 15.2 Kesme için atomik kabul bariyeri

1. Main/SessionActor aktif `session_epoch` değerini atomik artırır ve mevcut `generation_id` için `revoked` kaydı oluşturur.
2. Playback feeder yalnız `(session_id, current_epoch, active_generation_id)` eşleşen chunk'ları kabul eder. Bu predicate hem queue'ya eklemede hem callback öncesi per-chunk tüketimde geçerlidir.
3. Playback ring içindeki eski chunk'lar temizlenir, device API uygunsa pending buffer flush edilir; flush gecikmesi ölçülür.
4. `generation.cancel` sidecar'a gönderilir. Producer checkpoint veya token loop içinde cancellation flag'i kontrol ederek üretimi durdurur.
5. Geç gelen eski `audio.chunk` mesajları reddedilir; `stale_chunks_rejected` metriği artar. Bunların sadece log'a düşmesi yeterli değildir; playback barrier gerçekten devrededir.
6. Cancel acknowledgment timeout olursa sidecar generation/worker durumuna göre fail-safe restart ve model state cleanup planı işler.
7. Yeni konuşma turu ancak barrier güncellenip uygun session state'e dönüldüğünde başlatılır.

### 15.3 İptal akışı — hedef zaman çizelgesi

```text
User presses Stop    Main              Playback            Sidecar/Speech
       │                │                   │                      │
       ├─stop──────────►│                   │                      │
       │                ├─epoch++──────────►│                      │
       │                ├─flush────────────►│                      │
       │                ├─cancel generation───────────────────────►│
       │                │                   │    old chunk ◄───────┤
       │                │                   ├─reject stale         │
       │                │◄────────cancelled / late event──────────┤
       │◄──stopped──────┤                   │                      │
```

Bu çizim, gerçek Windows callback timing veya garantili örnek-örnek sessizlik iddiası değildir. Uygulamanın durdurma sonrası hoparlör tamponunu kaç ms'de boşalttığı gerçek cihazda ölçülür. Hedef performans sınırları [Speech Performance](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/PERFORMANCE.md) ve Live test raporunda deneysel olarak belirlenir.

### 15.4 Race testleri

- Aynı `stop` komutu 2, 10 ve 100 kez gönderilir; tek epoch değişimi politikası tutarlı ve tekrar idempotenttir.
- `audio.chunk` tam `epoch++` öncesi ve sonrasında gelir; yeni bariyer sonrası eski chunk hoparlöre girmez.
- Cancel sırasında device değişir; eski audio buffer yeni cihazda replay edilmez.
- Model tam EOS üretirken cancel gelir; `completed` ve `cancelled` iki ayrı terminal sonuç olarak aynı generation'a çift yazılamaz.
- IPC bağlantısı kopar; sidecar eski epoch'ta üretmeye devam etse bile Live playback engeller.
- Uygulama close olurken cancel ack hiç gelmez; bounded timeout ve kill uygulanır.

## 16. Speech SDK adapter: bugün ne çağrılabilir, yarın ne gerekecek?

**MEVCUT kod gerçekleri:** `kaiwen_voice.codec.mimi_codec.MimiCodec.from_pretrained`, `kaiwen_voice.training.checkpoint.load_checkpoint`, `kaiwen_voice.inference.generate.build_dialogue_prompt` ve `generate` vardır. `MimiCodec` referans codec'tir: 24 kHz, yaklaşık 12,5 codec frame/s, 8 codebook, her biri 2048 token. Şu an kendi KaiwenCodec'in eğitilmiş sürümü, public streaming session ve cached Transformer next-frame API'si yoktur.

### 16.1 Adapter'ın sorumluluğu

Adapter; çalışan Speech API'sini çağırır, tensör/PCM formatını doğrular, device/dtype veya inference context kurallarını uygular, cancellation ve telemetriye gerektiği kadar arayüz sağlar ve session actor'a typed output döndürür. Adapter, Speech modelinin attention, RoPE, codec RVQ algoritmalarını yeniden yazmaz. Model quality ve acoustic delay gibi bilimsel doğruluk kuralları Speech testlerinin sahibidir.

### 16.2 Mevcut batch kontrolün kavramsal çağrısı

```python
# MEVCUT import'lar: bu kod ancak doğru eğitim checkpoint'i ve
# audio extras/Mimi ağırlıkları mevcutsa ses üretir.
import torch
from kaiwen_voice.codec.mimi_codec import MimiCodec
from kaiwen_voice.inference.generate import build_dialogue_prompt, generate
from kaiwen_voice.training.checkpoint import load_checkpoint

model, step, payload = load_checkpoint("artifacts/compatible_checkpoint.pt", device="cpu")
model.eval()
codec = MimiCodec.from_pretrained("kyutai/mimi", num_codebooks=model.config.num_codebooks, device="cpu")

# PCM tensörü [B,C,S] ve 24k sample_rate, Live audio adapter tarafından hazırlanır.
# Bu satırlardaki input tensorünün temsili olması nedeniyle snippet tek başına
# çalışır bağımsız bir WAV command değildir.
with torch.inference_mode():
    user_codes = codec.encode(input_pcm_tensor, sample_rate=codec.metadata.sample_rate)
    prompt = build_dialogue_prompt(model, user_codes)
    response_codes = generate(model, prompt, max_new_frames=64, temperature=0.0)
    output_pcm_tensor = codec.decode(response_codes)
```

`input_pcm_tensor` bilerek bu örnekte tanımlanmamıştır: gerçek uygulamanın PCM decoder/resampler akışından gelecektir. Bu kod **SDK fonksiyonlarını gösteren parça örnek** olup yanıt kalitesi/süre/VRAM garantisi değildir. Gerçek CLI örneği Speech reposunda `scripts/infer_audio.py` dosyasıdır. `generate` şimdi full prefix recompute eder; `native_stream` ile eşdeğer değildir.

### 16.3 Hedef adapter arayüzü — PSEUDOCODE

```python
from dataclasses import dataclass
from typing import Protocol, AsyncIterator, Literal

Mode = Literal["fake", "batch_turn", "native_stream"]

@dataclass(frozen=True)
class AudioInput:
    pcm: bytes
    sample_rate_hz: int
    channels: int
    sample_format: str

@dataclass(frozen=True)
class AudioOutput:
    pcm: bytes
    sample_rate_hz: int
    channels: int
    sample_format: str
    generation_id: str
    is_final: bool

class SpeechRuntimeAdapter(Protocol):
    async def load_verified_release(self, release_dir: str) -> None: ...
    async def generate_batch(self, audio: AudioInput, generation_id: str) -> AudioOutput: ...
    async def stream(self, session_id: str, audio: AsyncIterator[AudioInput]) -> AsyncIterator[AudioOutput]: ...
    async def cancel(self, generation_id: str) -> None: ...
    async def close(self) -> None: ...
```

**Bu `Protocol` Live'da henüz yoktur.** Nihai API, Speech [API.md](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/API.md) ile birlikte stabilize edilir. `stream` metodu ancak Speech native stream implementation tamamlanınca capability olarak açılır. Python `async def` içine doğrudan senkron ağır model kodu koymak event loop'u bloke edebilir; inference ayrı worker/thread/process veya ölçülmüş doğru concurrency düzeni gerektirir. Cancellation için PyTorch kernel'lerinin preempt edilebildiği iddia edilmez; next safe boundary ve timeout belirlenir.

### 16.4 Model çıktısının doğrulanması

Çıktı PCM'si finite değerli, doğru dtype, beklenen sample rate ve boyut sınırında olmalıdır. Boş token üretimi (erken EOS) kullanıcıya sessizlik olarak satılmaz; `generation.empty_output` hatası/metriği ile görünür. Codec sample rate model profiliyle uyuşmuyorsa Live yeniden etiketleme yapmaz; açık dönüşüm veya release mismatch uygulamalıdır.

## 17. Model release yükleme, kaynak tahsisi ve atomik geçiş

Kaiwen Forge'un `kaiwen.model.release` manifesti **tek hedef şema** olarak önerilir. Tarihsel Speech API taslağındaki `kaiwen.speech.release` adı, 31-belge denetiminde kanonik örnek olmaktan çıkarılmıştır. **Kodda gerçek JSON Schema/Pydantic ve Golden Fixture MR0 kararı henüz yoktur**; üretim loader'ı bunlar doğrulanmadan uygulanmış sayılmaz. Eski adın sessiz alias olarak kabulü yasaktır. Registry'nin yayınlama izni ile Live'ın dosya okuma izni ayrı doğrulanır.

### 17.1 Model açılış akışı

1. Kullanıcı/yerel ayarlar yalnız `release_id` ile kayıtlı bir adayı işaretler.
2. Manifest boyutu, JSON tipi, supported schema/version ve güvenilen kaynak policy doğrulanır.
3. Model ağırlığı, codec ağırlığı, tokenizer/codebook mapping ve config dosyaları hash'lenir; tamamı eşleşmelidir.
4. `sample_rate_hz`, codec frame rate, codebook sayısı/boyutu, control token ID'leri, acoustic delay ve quantizer identity kontrol edilir.
5. Release izni ve lisans/dağıtım bilgisi değerlendirilir; yalnız hash güvenilir yayıncı kanıtı değildir.
6. Gerekli RAM/VRAM tahmini ve runtime capability uyumu kontrol edilir.
7. Düşük öncelikli staging context'te model açılır, kısa smoke inference yapılır; başarısızlıkta temiz kapatılır.
8. Yeni release yalnız yeni session'lar için atomik active pointer olur; açık session'a ağırlıklar yerinde değiştirilmez.
9. Başarısız hot-swap denemesinde son çalışan doğrulanmış release korunur.
10. Kullanıcıya gerçek model adı, codec, runtime mode ve warm-up durumu gösterilir.

### 17.2 2 GB VRAM hedefi ve fail-safe

Ağırlık dosyalarının toplam boyutu ile peak VRAM aynı şey değildir. CUDA allocator, runtime context, codec, KV cache, forward activations, conversion buffers ve UI dışı GPU rezervasyonları sayılır. GPU yetersizse donanım/precision seçenekleri gözden geçirilir; CPU fallback kullanıcıya açıkça belirtilir. Bir 50M FP16 modelin teorik ~100 MB ağırlık bellek tutması sistemin 2 GB VRAM'de kesin çalıştığını kanıtlamaz. 2 GB performans kabulü gerçek donanım ölçümüyle yapılır.

### 17.3 Model indirme ve güncelleme

Yükleme fonksiyonu varsayılan olarak internete erişmez. Model release indirme ayrı, kullanıcı onaylı, güvenilir kanal ve beklenen SHA-256 ile gerçekleşir. İndirme staging dizininde, resume destekli ve disk alanını kontrol ederek yapılır. Model onaylı hale gelmeden UI `ready` göstermeyecektir. Güncelleme Electron uygulaması ile model release'i birbirinden bağımsız versiyon alanlarına sahiptir.

## 18. Yerel transport alternatifleri ve teknik seçim kriterleri

Bu belgede tek nihai IPC transport'u dogmatik biçimde seçilmez. Başlangıçta uygulanması kolay bir **authenticated loopback** veya Windows named pipe tercih edilebilir. Her seçenek aynı JSON event ve logical PCM header contract'ını geçmelidir.

| Aday | Avantaj | Risk | Kanıt şartı |
|---|---|---|---|
| Localhost WebSocket + binary frames | TS/Python araç ekosistemi geniş; debug kolay | Yanlış bind, token/origin, reconnect ve binary framing | Windows firewall, port collision, auth, reconnect, p95 overhead. |
| Named pipes | Yerel kullanıcı ACL ve proses bağlamına uygun | Windows-specific implementation ve paketleme | ACL, process lifetime, short read/write, client impersonation. |
| Stdio framed protocol | Tek child process ile basit bootstrap | stdout log karışması, backpressure, crash recovery | Framing, stderr ayrı, child kill/restart. |
| Shared memory + control pipe | Düşük copy potansiyeli | Ownership, race, stale memory, cleanup karmaşıklığı | Stress/kill/cancel testleri ve gerçek performans ölçümü. |

En hızlı benchmark sonucu tek kriter değildir. Güvenlik, hata kurtarma, geliştirme maliyeti, installer testi ve 2 GB cihaz sınıfında gözlenen gerçek gecikme kararı birlikte verir. Aynı anda üç transport implementasyonu yazmak V1 için gereksizdir; birini seçip contract'ı stabil tut.

### 18.1 Reconnect ve session geçerliliği

Transport koparsa artık capture ve playback yolunun karşı uca bağlı olduğunu varsayma. Session `disconnected` alt duruma alınır; mikrofon gizlice veri biriktirmeye devam etmez. Yeni transport bağlantısında el sıkışma, auth, release id ve `session_epoch` doğrulanır. Önceki stream chunk'ları replay edilmez; codec state/KV cache restore ancak Speech tarafından özel recovery capability açıklanırsa mümkündür.

### 18.2 Bounded payload ilkesi

Kontrol JSON max size, PCM frame max size, maksimum eşzamanlı request, timeout ve rate limit açık konfigürasyondur. Başlık okunmadan büyük bellek allocation yapılmaz. Sık sample gönderme IPC'de mesaj sayısını gereğinden büyütürse paketleme/multiplex yapılabilir; audio örnek süresini değiştirip gürültüde sessizlik eklenmez.

## 19. Güvenli Electron mimarisi ve preload sözleşmesi

V1 Electron BrowserWindow için `contextIsolation: true`, `nodeIntegration: false`, mümkünse `sandbox: true`, dar CSP ve navigation/windowOpen policy gerekir. Gereksiz Node API veya güncelleme token'ı renderer'a açılmaz. Seçilen audio capture backend'in Electron sandbox ile gerçek uyumluluğu kanıtlanmadan sandbox'ı sessizce kapatmak kabul edilmez; gerekli istisna kayıt altına alınır ve alternatif I/O aranır.

### 19.1 Preload yüzeyi — HEDEF, pseudocode

```typescript
// HEDEF API: gerçek preload ve main handler'ları henüz yazılmadı.
export type RuntimeMode = "fake" | "batch_turn" | "native_stream";
export interface DeviceSummary { id: string; label: string; kind: "input" | "output" }
export interface LiveBridge {
  listDevices(): Promise<DeviceSummary[]>;
  requestMicrophonePermission(): Promise<{ granted: boolean }>;
  startSession(releaseId: string, mode: RuntimeMode): Promise<{ sessionId: string }>;
  finishTurn(sessionId: string, turnId: string): Promise<void>;
  stopPlayback(sessionId: string): Promise<void>;
  cancelGeneration(sessionId: string, generationId: string): Promise<void>;
  closeSession(sessionId: string): Promise<void>;
  onSessionEvent(listener: (event: unknown) => void): () => void;
}
```

`event: unknown`, runtime parsing/güvenli schema ile birlikte kullanılır; `any` ile kontroller atlanmaz. `releaseId`/`sessionId` arbitrary file path değildir; server-side authorization ile kontrol edilir. Main handler request argümanlarını doğrulamadan OS API'sine veya sidecar'a göndermez. `onSessionEvent` unsubscribe'ı React lifecycle'da çağrılır; yoksa her remount iki kat event alabilir.

### 19.2 Dosya ve link güvenliği

File dialog gerçek OS kontrolünden döner; ancak her path otomatik model/codec erişimi anlamına gelmez. Release directory kökü, manifest açıldıktan sonra resolve/symlink denetimleri, MIME/type ve byte cap uygular. Harici linkler izinli `https` scheme ile sistem tarayıcısına açılır; uzak web sayfasının `nodeIntegration` yetkisi yoktur. Electron navigation tüm URL'leri app window içine yüklemez.

### 19.3 Secret yönetimi

Local loopback auth token, seçili modelin dağıtım kredansiyeli veya gelecekteki Agent API anahtarları Electron renderer localStorage'ında saklanmaz. OS credential vault veya korumalı process secret tercihi kaydedilir. Debug loglarında token, ses içeriği, açık tam local path veya kişisel konuşma metni bulunmaz. Token sızıntısı tespit edilirse rotate/kill session/transport politikası vardır.

## 20. Windows audio device lifecycle ve cihaz değişimi

Mikrofon ve hoparlör seçimi UI ayarından fazlasıdır. Windows kullanıcı izinleri, default device değişimi, USB/Bluetooth bağlantı kopması, exclusive/shared mode, buffer size, channel layout ve sample rate davranışı sürücüye göre değişir. Live, aygıt ID'sinin kalıcı olacağını veya ses seviyesinin bütün driver'larda aynı aralıkta olduğunu varsaymamalıdır.

### 20.1 Capture açma akışı

1. Kullanıcı buton veya açık onboarding ile mikrofon kullanımını başlatır.
2. OS permission durumunu sorgula; gerekirse görünür izin akışını tamamla.
3. İstenen device ID'nin hâlen erişilebilir olduğunu doğrula; değilse kullanıcıya varsayılan cihaza geçiş öner.
4. Native format, sample rate, channels, callback period ve device latency bilgisini al.
5. Gerekli resampler ve ring capacity'yi gerçek format üzerinden oluştur.
6. Kısa capture probe yap; ilk sample'ın geldiğini doğrula. `start()` çağrısı dönmesi tek başına başarılı kayıt demek değildir.
7. `device.capture_started` event'i ve gerçek aygıt kimliği ile `listening` durumuna geç.
8. İzin geri çekilir veya cihaz kaybolursa callback'i güvenli kapat, input turn'ü açık hata/partial policy ile sonlandır, UI'a durumu bildir.

### 20.2 Playback açma akışı

1. Kullanıcı tarafından seçili output device doğrulanır.
2. `sample_rate/channel/format` desteği sorgulanır; dönüşüm gerekiyorsa açık transform oluşturulur.
3. Playback queue ve priming policy hazırlanır; cihazda ilk PCM kabulü ölçülür.
4. Output buffer boşaldığında underrun sayılır; varsayılan concealment sessizliği metriği gizlemez.
5. `playback.started` mümkün olduğunca fiziksel output callback/sample verisine bağlanır; sadece `enqueue` olmasıyla eşit sayılmaz.
6. Final chunk teslimi ile son sample'ın gerçekten cihazdan tüketilmesi farklı olaylardır; `playback.completed` buna göre üretilir.

### 20.3 Device hot-swap ve failure matrix

| Olay | Güvenli davranış | Kayıt/metrik |
|---|---|---|
| Mikrofon USB kablosu çıkarılır | Capture durur, izinler kontrol edilir; session kontrollü `ready`/error | `device_lost`, missing_samples |
| Hoparlör kaybolur | Output durur; kullanıcıya cihaz seçimi; gerekiyorsa queue flush | `output_device_lost`, stale PCM |
| Default device değişir | Otomatik geçiş yalnız açık politika varsa | Device old/new ID, resampler reset |
| Bluetooth gecikmesi artar | Buffer profilini ölç; “sıfır gecikme” iddiası verme | Audio device output latency |
| İzin geri çekilir | Device kapatılır; ses taşınmaz | `permission_revoked` |
| Sample rate aniden değişir | Yeni stream/negotiation; eski header'ı yeniden etiketleme | `format_renegotiation` |
| OS suspend/resume | Güvenli stop, reconnect handshake; mic otomatik açılmamalı | `suspend_resume` |
| İki uygulama aynı cihazı kullanır | Shared/exclusive policy ve kullanıcı mesajı | `device_busy` |

### 20.4 Echo ve akustik sorunlar

Speaker'dan çalan ses capture'a geri girerse VAD yanlış barge-in başlatabilir. V1 half-duplex veya kulaklık ile kanıt üretilebilir. Full-duplex auto barge-in ancak echo cancellation performansı, cross-talk, akustik feedback ve kullanıcı sesini kaçırmama testleriyle açılır. Gürültü temizleyici eklemek tek başına ürün kalitesini garanti etmez; konuşma doğallığına zarar veren artefaktları dinleme testi ölçer.

## 21. Sidecar process supervisor: başlatma, health, restart ve shutdown

Electron main, sidecar'ın tek sahibidir. Renderer veya bağımsız browser process yan servis başlatmaz. Supervisor; packaged executable path, process PID, startup timeout, health, exit code, abnormal restart count ve session cleanup'ı kaydeder. Birden fazla pencere açılması aynı GPU modelinin yanlışlıkla ikinci kez yüklenmesine neden olmamalıdır.

### 21.1 Başlatma sırası

1. Runtime dosya bütünlüğünü installer manifestine göre kontrol et; user config ile executable path override izin verme.
2. IPC adresini güvenle seç; loopback port ise doğrudan bind edip gerçek portu child'a bildir; tahmini sabit portla çakışma riski yaratma.
3. Per-instance auth capability token/pipe ACL oluştur.
4. Child process'i shell kullanmadan, kısıtlı env ile başlat; stdout/stderr'i ayrı, bounded log collector'a gönder.
5. Minimum `/health` veya typed `runtime.hello` handshake bekle; doğru instance ID ve protocol version doğrula.
6. Runtime'a release manifesti seçme/yükleme komutu gönder; device profile ve capability negotiation yap.
7. Modelin gerçekten hazır olduğunu `runtime.ready` doğrulayınca session açılabilir.
8. Başlatma başarısızlığında kullanıcıya kısa hata kodu ve güvenli retry butonu sun; otomatik sonsuz restart döngüsü kurma.

### 21.2 Crash recovery

Bir sidecar crash'i OS audio callback'ine taşmamalıdır. Main input/output akışlarını güvenli kapatır, device callback'inden erişilebilecek eski backend ring'lerini serbest bırakmadan önce referansların bittiğini doğrular, aktif generation'ları iptal olmuş sayıp yeni epoch bariyeri kurar. Restart politikası exponential backoff + sınırlı deneme sayısıdır; aynı model sürekli OOM veriyorsa retry yerine kullanıcıya precision/CPU önerilir. Crash sonrası önceki session'a konuşma state'i restore edilmiş gibi davranılmaz.

### 21.3 Graceful shutdown

```text
Quit requested
 → UI stops new commands
 → capture disabled + device handle release
 → session epoch barrier / stale outputs refused
 → playback queue stop + optional drain or silence policy
 → generation.cancel (bounded acknowledgement)
 → sidecar session.close / model unload
 → IPC close + child process normal exit
 → timeout ? OS process-tree kill
 → Electron terminates, no orphan/mic handle
```

Normal kapatmada model dosyaları diskten silinmez. `close` komutu tekrar edilirse idempotent davranır. GUI kapanınca OS process-tree yoklama ile orphan child kalmadığı Windows e2e testinde kanıtlanır. Crash durumunda log klasöründe kişisel PCM, token veya transkript sızıntısı bulunmadığı ayrı kontrol edilir.

### 21.4 Session ve process lifecycle neden ayrı?

Uygulama açık ve runtime hazırken kullanıcı konuşma oturumunu kapatabilir; sidecar yine model tutabilir veya enerji tasarrufu politikasına göre unload olabilir. Bir model release seçiminin değişmesi oturumu kapatmayı gerektirebilir ama app quit anlamına gelmez. Aksi yönde sidecar yeniden başlatılırken UI açık kalabilir ancak ses dinleyip konuşuyormuş gibi gösterilmez.

## 22. Hata sınıfları, kullanıcı mesajları ve yeniden deneme sınırları

Hata türü machine-readable `code`, güvenli `message`, `retryable`, `correlation_id`, hangi state'te oluştuğu ve önerilen recovery action ile taşınır. Stack trace, GPU driver path, raw konuşma içeriği, auth secret veya tam yerel kullanıcı dizini UI error'a taşınmaz. Kullanıcıya anlaşılır mesaj, geliştiriciye kişisel veri içermeyen diagnostic ID verilir.

| Kod sınıfı | Örnek tetik | Oturum kararı | Yeniden deneme |
|---|---|---|---|
| `permission.denied` | Mikrofon reddedildi | `ready` | OS izin düzeltildikten sonra. |
| `device.input_lost` | Capture bağlantısı koptu | Capture altstate failed | Yeni cihaz seçerek. |
| `device.output_unavailable` | Hoparlör meşgul/yok | Generation output saklama policy | Yalnız sınırlı süre. |
| `transport.protocol_mismatch` | Desteklenmeyen major | Init fail | Uyumlu sürüm gerekir; otomatik deneme yok. |
| `transport.auth_failed` | Yanlış per-instance token | Bağlantı reddedilir | Yeni handshake ve token. |
| `audio.invalid_frame` | Sample byte sayısı uyuşmuyor | Akış reddi | Aynı bozuk chunk yeniden kabul edilmez. |
| `audio.queue_overflow` | Input/output queue taşıyor | Turn abort veya explicit drop | Root-cause düzeltme. |
| `model.release_invalid` | Hash/manifest/codec mismatch | Init fail | Doğru release indirilmeli. |
| `model.out_of_memory` | GPU bellek yetmedi | Generation fail, state cleanup | Lower precision/CPU, kontrollü. |
| `generation.empty_output` | Erken EOS; hiç ses yok | User-facing error | Farklı prompt/model quality incelemesi. |
| `generation.cancel_timeout` | Model cancellation ack yok | Runtime reset veya process kill | Sınırlı, explicit. |
| `sidecar.crashed` | Python process çıktı | Session invalid | Bounded supervised restart. |
| `playback.underrun` | Buffer ses yetişmedi | Gerektiğinde `speaking` sürer, metrik artar | Buffer/RTF profili iyileştir. |
| `privacy.unauthorized_capture` | İzinsiz açık mic durumu | Fatal stop | Güvenlik olayı, sessiz retry yok. |

### 22.1 Retry hiçbir zaman çift çıktı üretmemeli

`command_id` idempotency ve `generation_id` kontrolü birlikte kullanılır. Aynı turda network timeout sonrası `generation.start` tekrar edilirse önceki generation'ın durumu sorgulanır veya yeni ID ile önceki attempt açıkça iptal edilir; aynı response iki kez oynatılmaz. `session.open` retry'si iki model kopyası veya iki audio device stream oluşturmamalıdır.

### 22.2 Kullanıcıya gösterim

Hata metni etken odaklıdır: “Mikrofon izni verilmedi; Windows izinlerini kontrol edin”, “Model ve codec sürümleri uyumsuz”, “Hoparlör bağlantısı kesildi”, “Bu cihazda seçili model için bellek yetmedi” gibi. Model bulunamıyorsa fake audio'ya sessizce geçip kullanıcıyı gerçek cevap almış gibi yanıltma; demo modu açık etiketlenir.

## 23. Telemetri, zaman ölçümü ve bilimin ayrı sorumlulukları

Hız için birden çok farklı saat noktası bulunur. Bunlar birbirine karıştırıldığında performans değerlendirmesi sahte iyileşme gösterir:

| Event | Sahip | Anlam |
|---|---|---|
| `capture.first_sample` | Device | Mikrofon gerçekten sample aldı. |
| `turn.finish_requested` | UI/Main | Kullanıcı tur bitişi istedi. |
| `turn.input_finalized` | Capture/adapter | Son input sample ve turn flush tamamlandı. |
| `generation.started` | Speech adapter | Model üretim attempt'i başlatıldı. |
| `generation.first_token` | Speech | İlk ses token'ı çıkarıldı; henüz duyulabilir değil. |
| `codec.first_decoded_pcm` | Speech | İlk decoded PCM üretildi. |
| `transport.first_output_arrived` | Live | İlk output PCM main tarafına geldi. |
| `playback.first_enqueued` | Live | İlk PCM playback queue'ya yazıldı. |
| `playback.first_device_sample` | Audio | İlk sample device backend tarafından tüketildi/sunuldu. |
| `playback.final_device_sample` | Audio | Son çıktı sample'ı tamamlandı. |

**TTFA tanımları:** `turn.input_finalized → first_decoded_pcm` model/codec hazırlık süresi için; `turn.finish_requested → playback.first_device_sample` kullanıcıya dönük uçtan uca gecikme için ölçülebilir. Her rapor başlangıç/bitiş olaylarını, clock domain ve sync yöntemini belirtir. Farklı proseslerin `monotonic_ns` sayacını doğrudan çıkarmak geçerli ölçüm değildir. Tek process içi timer veya açık clock alignment tercih edilir.

### 23.1 RTF ve üretim hızı

`RTF = processing_wall_time / emitted_audio_duration`. Codec encode/decode, Transformer ve transport ayrı RTF/süre parçalarıyla profillenebilir. RTF `1.0` altı olması her zaman ilk sesin çabuk geldiğini garanti etmez; uzun prefill veya büyük playback buffer TTFA'yı yükseltebilir. Batch ve streaming RTF kapsamı ayrı etiketlenir. Chunked playback kendi başına model hızını değiştirmez.

### 23.2 UI performansıyla ses performansı ayrılır

Renderer FPS, React commit latency, waveform çizimi; `audio_callback_p99_ms`, `ipc_p95_ms`, `playback_underruns` ve GPU inference metriklerinden ayrıdır. UI 60 FPS'e çıkarken mikrofon sample drop yükselirse bu başarı değildir. Live [Speech Performance](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/PERFORMANCE.md) sözlüğüne uyumlu ölçümler yapar, fakat donanım duyulan ilk ses metriğinin sahibidir.

### 23.3 VRAM ölçüm koşulları

Model parametre sayısı, precision, codec, session uzunluğu, KV cache uzunluğu, input sample rate, output device, OS, GPU sürücü ve measurement tool rapora yazılır. RTX 4050 6 GB geliştirme bilgisayarı performansı, 2 GB VRAM sınıfı düşük bellek cihazına otomatik genellenemez. CPU fallback çalışsa bile ayrı mod olarak kullanıcıya sunulur. Warm/cold run dağılımı ve p50/p95 birlikte kaydedilir.

### 23.4 Hedef performans raporu — JSON fixture

```json
{
  "schema_name": "kaiwen.live.performance.run",
  "schema_version": "1.0.0",
  "session_id": "fixture-session",
  "generation_id": "fixture-generation",
  "runtime_mode": "batch_turn",
  "model_release_id": "fixture-not-a-real-release",
  "hardware": {
    "os": "Windows",
    "gpu": "test-profile",
    "precision": "fp16"
  },
  "timing": {
    "measurement_status": "not_measured",
    "end_to_end_ttfa_ms": null,
    "first_token_ms": null,
    "real_time_factor": null,
    "sample_count": 0
  },
  "queues": {
    "input_dropped_samples": 0,
    "playback_underruns": 0,
    "stale_chunks_rejected": 0
  },
  "memory": {
    "peak_vram_bytes": null,
    "measurement_status": "not_measured"
  }
}
```

Sıfır değerli kuyruk sayaçları bu örnekte yalnız test fixture başlangıç durumudur. `null` ölçülmemiştir; `0 ms` sonucu yerine kullanılmaz. Bu JSON gerçek benchmark kaydı değildir. Veri saklama politikası diagnostik metrikleri içerse bile ham ses ve transkript varsayılan olarak kaydedilmez.

## 24. Config ve runtime feature gate politikası

Konfigürasyon UI, Electron main ve Python sidecar arasında ayrılır; güvenlik kararlarının sahibi her zaman karşılık gelen privileged process'tir. Renderer flag'i değiştirip sidecar'da `native_streaming=true` oluşturamaz. Kalıcı ayarlar hassas olmayan kullanıcı tercihleri; geçici session flag'leri her açılışta handshake'den; model capability'si doğrulanmış release'ten gelir.

### 24.1 Örnek runtime config — HEDEF

```yaml
schema_version: "1.0.0"
runtime:
  mode: "batch_turn"
  max_concurrent_sessions: 1
  sidecar_start_timeout_ms: 30000
  command_ack_timeout_ms: 5000
  graceful_shutdown_timeout_ms: 10000
audio:
  transport_sample_rate_hz: 24000
  transport_channels: 1
  transport_format: "pcm_s16le"
  preferred_capture_chunk_ms: 20
  capture_buffer_ms: 200
  output_buffer_ms: 200
  auto_start_microphone: false
privacy:
  persist_raw_audio: false
  persist_transcripts: false
  diagnostics_opt_in: false
agent:
  enabled: false
  require_tool_approval: true
```

Örnek sayılar başlangıç profilidir; bilimsel benchmark veya ürün default'u olduğu kanıtlanmamıştır. Son uygulama schema'sı karar anında sürümlenecek, range/type validation ve değişiklik migrasyonu test edilecektir. Kullanıcı tercihinden bağımsız `max_sessions` ve `allow_external_bind` gibi kritik güvenlik ayarları UI'dan keyfi yükseltilemez.

### 24.2 Feature gate bağımlılıkları

- `native_streaming = true` için Speech release runtime capabilities ve end-to-end cached codec/Transformer testi gerekir.
- `agent_bridge = true` için Agent adapter, explicit intent, uygun speech-output yolu ve onay akışı gerekir.
- `barge_in_auto = true` için echo handling, VAD/overlap değerlendirmesi ve gerçek cihaz testleri gerekir.
- `cpu_fallback = true` ise CPU release/inference parity ve UX gecikmesi ölçülmüş olmalıdır.
- `experimental_codec = true` yalnız uygun aynı codec ağırlığıyla eğitilmiş modelde etkin olabilir.

## 25. Agent köprüsü: modal sınır, concurrency ve output sorunu

Fast Path varsayılan olarak Speech'in öğrendiği doğal konuşma örüntülerini kullanır. Agent Path ise ancak kullanıcının açık komutu, ayrıca doğrulanmış intent adapter'ı veya ileride eğitilmiş model kontrol token'ı ile başlar. Speech bugün ses tokenlarından güvenilir `agent_requested` arayüzü sunmaz. Live bir transkripsiyon modeli çalıştırmıyorsa kullanıcı sesinden tool command text çıkarabileceğini varsayamaz.

### 25.1 Bağımsız Agent flow

```text
User speech / UI explicit action
  ├─ Fast Path → Speech respond as native audio
  └─ Agent requested? → permission and intent validation
                       → async Agent request (separate queue/timeouts)
                       → tool result + approval status
                       → audio response adapter capability?
                           ├─ YES → speech model supported conditioning → playback
                           ├─ Optional declared TTS bridge → voice, labeled non-native
                           └─ NO → honest on-screen text, no fake voice claim
```

Agent uygulamasının yetenekleri [Agent repo](https://github.com/ImtheKaiwen/kaiwen-agent) içindeki kod/sözleşmelere göre değerlendirilir. Tool çağrısı renderer'dan keyfi JSON command ile doğrudan işletilmez. Agent bir web araması yapacaksa mikrofon/playback işlemlerini durdurmadan kendi timeout ve cancellation mekanizması çalışır. Agent yanıtının mutlaka Türkçe ses olarak üretilebildiği iddia edilmez: modele metin koşullandırma eğitimi gerekebilir veya açıkça opsiyonel TTS bridge gerekir; bunlar Native Speech'in aynı ürün kabiliyeti değildir.

### 25.2 İptal ilişkisi

Kullanıcının `playback.stop` eylemi Agent'ın hâlihazırda dış sistemde başlatılmış yetkili işini otomatik olarak iptal etmez. `cancel_generation` Speech çıktı üretimini durdurur; `cancel_agent_task` varsa ayrı komuttur. Ödeme, e-posta gönderme veya başka etkili aksiyonlar her zaman açık yetki, tool sonucunu doğrulama ve hatalı retry'lerde idempotency gerektirir. İki farklı katmanın cancellation'ını tek `stop_all()` fonksiyonuna saklamak denetlenebilirliği azaltır.

## 26. Mahremiyet, tehdit modeli ve yetki azaltma

Ses verisi kişisel bilgi içerebilir. Live'ın mahremiyet politikası **sesin yerelde işlenmesi**, yalnız seçili oturum süresince tutulması ve kullanıcı açık istemedikçe sesin, transkriptin veya embedding'in diske kaydedilmemesi temelindedir. Crash dump ve debug log'larının da bu bilgileri taşıyabileceği unutulmaz.

| Tehdit | Saldırı yüzeyi | Tedbir | Negatif test |
|---|---|---|---|
| Mic gizlice açılır | UI state/permission mismatch | Kullanıcı eylemi, OS permission ve gerçek LED/state uyumu | Session olmadan capture reddi |
| Yanlış local process bağlanır | Loopback/pipe | Auth token/ACL/origin/pid policy | Unauthorized client reject |
| Renderer keyfi dosya okur | Electron bridge | Strict allowlist, path sandbox, schema validation | `../` ve symlink saldırıları |
| Kötü amaçlı model dosyası | Manifest/checkpoint | Trusted release, checksum, safe deserialization, sandbox | Tamper/hardlink/symlink/oversized |
| Bellek taşması | PCM parser/queue | Header-before-allocation ve byte cap | Huge length/fragment flood |
| Eski ses replay edilir | IPC delayed frames | Epoch/generation barrier | Late chunk injection |
| Secret sızar | Log/env/renderer | OS protected storage, redaction | Static scan/log snapshot |
| Agent yetki aşımı | Tool adapter | Explicit user approval & capability policy | Unapproved tool reject |
| Telemetry kişisel veri taşır | Diagnostics | Aggregated metrics, opt-in, retention | Export of diagnostics snapshot |
| Mic açık unutulur | Crash/quit/device error | Fail-safe device close + watchdog | OS process kill and handle check |

**Threat model notu:** Hash dosyanın bütünlüğünü gösterir ama trust root olmadan kaynağının güvenilir olduğunu kanıtlamaz. Aynı şekilde loopback bağlantısı cihaz içindeki diğer yazılımları otomatik olarak dışlamaz. IPC erişim denetimi, model release güveni ve renderer sandbox birbirinden bağımsız güvenlik kapılarıdır.

### 26.1 Sesin diskte saklanması ve hata raporu

Varsayılan `persist_raw_audio=false`; test fixture'ları ve kullanıcı tarafından açıkça kaydet seçilen sesler ayrı saklama ve silme politikasına sahiptir. Sessiz `debug.wav` veya `last_user_audio.wav` kaydı yasaktır. Telemetry raporu, sample count ve gecikme ölçüsü içerebilir; konuşma içeriği ve konum içermemelidir. İsteğe bağlı sorun raporu gönderilecekse kullanıcıya içerik açıkça gösterilir.

### 26.2 Model doğrulama saldırıları

Release paketinde `../` path, çok büyük manifest, symlink dışarı yönlendirmesi, başka süreç tarafından son anda değiştirilmiş dosya, yanlış `model.pt` ve sahte codec metadata fixture'ları çalıştırılmadan release loader güvenli sayılmaz. Bütünlük doğrulama sonrası dosyaların değişmesini önleyen atomik snapshot/readonly staging politikası gerekir.

## 27. Windows paketleme ve sürüm güvenliği

Bir geliştirici bilgisayarında `python scripts/infer_audio.py` çalışması, kullanıcının indirdiği `Kaiwen Live.exe` dosyasının modeli açabileceği anlamına gelmez. Windows installer; Electron JS bundle, Python runtime veya ayrı sidecar exe, PyTorch bağımlılıkları, codec/model artifact yönetimi, FFmpeg/resampler gereksinimleri, doğru DLL'ler, OS permission ve updater stratejisini açıkça kapsar.

### 27.1 Build zinciri

1. Paket bağımlılıkları ve sürümleri kilitlenir; React/Electron ve Python bağımlılıkları ayrı doğrulanır.
2. Sidecar Windows target üzerinde pyinstaller veya uygun araçla paketlenir; tek exe yöntemi import/DLL testinden geçmelidir.
3. Speech SDK import, `torch`, codec audio extras ve model format compatibility Windows temiz VM/runner'da sınanır.
4. Model release bundling kararı yapılır: büyük ağırlıkların installer'a gömülmesi ile ayrı doğrulanmış indirme ikisi de ölçülür.
5. Elektron uygulaması nodeIntegration kapalı, preload ve CSP doğru şekilde paketlenir.
6. Ürün sürümü, sidecar protokol aralığı ve model release gereksinimi birlikte manifestte tutulur.
7. Installer uygulamayı kapatırken sidecar'ı orphan bırakmaz; uninstall kullanıcı dataset/model/cache silme kararını açıkça sorar.
8. Update staging, imza doğrulama, rollback ve failure recovery tested olmadan “self-updating” iddiası açılmaz.

### 27.2 Ayrık sürüm alanları

`app_version`, `sidecar_version`, `protocol_version`, `speech_sdk_version`, `model_release_id`, `codec_release_id` ayrı alanlardır. Hepsi `v1.0.0` yazıldı diye uyumlu değildir. Compatibility matrix testleri ve release manifest asgari sürüm kontrolleri yapılır. Eski Live app yeni model release'i yükleyemiyorsa açık hata gösterir; manifest yeniden adlandırılarak uyumlu gibi davranılmaz.

### 27.3 Windows ortamı ve dosya konumları

Kullanıcı verisi uygulama-data konumunda, binary dosyalar installer konumunda, model artifact'leri doğrulanmış model-store kökünde kalır. Geliştirici `cwd` dizini ile üretim model storage'ı aynı varsayılmaz. OneDrive veya senkronize klasörlerde dosya lock/deletion yarışları yaşanabilir; model store'un atomik güncellemesi kullanıcı tarafından taşınmışsa önce filesystem capability kontrol edilir.

## 28. Hata enjeksiyonu ve test seviyeleri

Testler `unit` (durum makinesi/format), `contract` (TS↔Python), `integration` (main↔sidecar), `hardware` (gerçek mikrofon/hoparlör), `fault injection` (kill/network/device) ve `research` (Speech native streaming parity) olarak ayrılır. CI'nin headless audio fixture suite'i gerçek kullanıcıya duyulan sesi kanıtlamaz. Fiziksel cihaz doğrulaması Windows pilot makinesinde kanıt artifact'i ile yürütülür.

### 28.1 Test matrisi — LIVE-ARCH-001 … LIVE-ARCH-042

| ID | Senaryo | Geçiş koşulu |
|---|---|---|
| LIVE-ARCH-001 | Desteklenen protocol handshake | Tek doğru capability snapshot oluşur. |
| LIVE-ARCH-002 | Yanlış major version | Model/mic açılmadan reddedilir. |
| LIVE-ARCH-003 | Yanlış token | Sidecar bağlantıyı açmaz. |
| LIVE-ARCH-004 | Unknown event | Typed unsupported, crash yok. |
| LIVE-ARCH-005 | Büyük control payload | Memory cap öncesi reddedilir. |
| LIVE-ARCH-006 | PCM16 24 kHz/20 ms geometri | 480 sample ve 960 bytes hesapları eşleşir. |
| LIVE-ARCH-007 | Float32 NaN/Inf | Geçersiz PCM doğrulanıp reddedilir. |
| LIVE-ARCH-008 | Header length ile payload farkı | Frame yutulmadan hata döner. |
| LIVE-ARCH-009 | Sequence duplicate | Ses ikinci kez dinletilmez. |
| LIVE-ARCH-010 | Out-of-order PCM | Açık policy, yanlış sample timestamp yok. |
| LIVE-ARCH-011 | Missing sequence | Dropped sample/discontinuity işaretlenir. |
| LIVE-ARCH-012 | Capture ring full | Callback bloklanmaz, sayım yükselir. |
| LIVE-ARCH-013 | Playback ring empty | Underrun ölçülür, deadlock yok. |
| LIVE-ARCH-014 | UI render 5 FPS'e düşer | Capture playback realtime yol sağlam kalır. |
| LIVE-ARCH-015 | Session `closed → listen` | Geçersiz geçiş reddedilir. |
| LIVE-ARCH-016 | Aynı `turn.finish` iki kez | Yeni generation çift başlatılmaz. |
| LIVE-ARCH-017 | `initialize` ile `close` yarışır | Sonuç closed, orphan yok. |
| LIVE-ARCH-018 | `stop` ile output chunk yarışır | Eski chunk dinletilmez. |
| LIVE-ARCH-019 | İptal sonrası 100 geç chunk | Tamamı epoch kontrolünden geçemeyip atılır. |
| LIVE-ARCH-020 | `generation.cancel` timeout | Fail-safe cleanup/restart uygulanır. |
| LIVE-ARCH-021 | `playback.stop` | Mic otomatik kapanmaz, model cancel bağımsızdır. |
| LIVE-ARCH-022 | `microphone.disable` | Capture kapanır, output kontrolü bozulmaz. |
| LIVE-ARCH-023 | `session.close` tekrarı | İdempotent, resource leak yok. |
| LIVE-ARCH-024 | OS mic izni reddi | Input stream başlamaz; UI gerçek hata gösterir. |
| LIVE-ARCH-025 | Capture cihazı çıkarılır | Oturum kontrollü recovery ve açık error. |
| LIVE-ARCH-026 | Playback cihazı çıkarılır | Queue/cancel state tutarlı ve hata görünür. |
| LIVE-ARCH-027 | Device sample rate değişir | Negotiation/resampler reset, yanlış PCM yok. |
| LIVE-ARCH-028 | OS suspend/resume | Mikrofon gizlice geri açılmaz. |
| LIVE-ARCH-029 | Sidecar kill | Main session invalid; Mic/Playback safely stopped. |
| LIVE-ARCH-030 | Sidecar restart fırtınası | Bounded retry; sonsuz loop yok. |
| LIVE-ARCH-031 | Model SHA-256 yanlış | Ağırlık yüklenmeden reddedilir. |
| LIVE-ARCH-032 | Codec ID eşleşmez, Q/K eşit | Release reddedilir. |
| LIVE-ARCH-033 | Manifest path traversal | Model store dışına çıkılmaz. |
| LIVE-ARCH-034 | Checkpoint güvenilmeyen pickle | Güvenli loader/format policy reddi. |
| LIVE-ARCH-035 | CUDA OOM | Bellek serbest, kullanıcıya policy uygun fallback. |
| LIVE-ARCH-036 | Real model erken EOS | Sessiz başarı etiketi yok; typed empty output. |
| LIVE-ARCH-037 | Fake runtime | Gerçek model capability'si açık gösterilmez. |
| LIVE-ARCH-038 | Chunked WAV | Native streaming olarak etiketlenmez. |
| LIVE-ARCH-039 | Measured TTFA | Başlangıç/bitiş ve clock domain belgeli. |
| LIVE-ARCH-040 | Installer clean Windows | Sidecar, ses, model ve izin zinciri açılır. |
| LIVE-ARCH-041 | App quit | Mic handle ve sidecar process kalmaz. |
| LIVE-ARCH-042 | Debug logs | Ses bytes, transkript, secret ve tam kişisel path sızmaz. |

Önce unit/contract, sonra fake integration, daha sonra gerçek Windows hardware suite uygulanır. Başarısız testler `skip` ile görünmez yapılmaz; neden ve iş sahibi kayıt altına alınır. Fiziksel device testleri CI runner'da desteklenmiyorsa `manual/hardware-required` adıyla raporlanır, `passed` sayılmaz.

## 29. CI kalite kapıları ve contract fixture yaklaşımı

Başlangıçta test framework ve package manager'lar seçilince ilgili komutlar gerçek repo script'lerine yazılır; bugün var olmayan `npm run test:e2e` komutu çalışmış gibi gösterilmez. Önerilen kalite kapıları:

- TypeScript: strict typecheck, ESLint, unit/contract tests ve Electron build.
- Python: `ruff`, `pyright` veya `mypy` tutarlılığı, pytest, JSON schema/PCM parser fuzz fixture'ları.
- Contract: sürümlü golden JSON control fixture, golden PCM binary byte dizisi ve TS/Python encode/decode eşleştirmesi.
- Security: Electron permissions/CSP, package audit, path traversal/IPC auth negatif testleri, secret scanning.
- Integration: fake sidecar start/stop, version negotiation, graceful close ve forced crash, stale-output testleri.
- Packaging: Windows CI release candidate; temiz OS VM/runner'da gerçek sidecar executable smoke.
- Hardware: gerçek mikrofon-hoparlör testleri ve delay/VRAM profil kaydı; yalnız uygun cihazda çalışır.

### 29.1 Golden fixture versiyonlama

Fixture'ların her biri açık `schema_version` ve oluşturucu versiyon içerir. Bir protobuf veya custom binary frame layout'u seçilirse bir byte değişikliği contract diff gerektirir. Codec model output deterministik değilse ses dalga biçimini bitwise karşılaştırmak yerine uygun signal tolerance, sequence consistency ve sample geometry kullanılır. Binary header parser deterministik kalmalıdır.

### 29.2 Geriye uyumluluk matrisi

`client N ↔ sidecar N`, `client N ↔ sidecar N-1`, `client N-1 ↔ sidecar N` konfigürasyonları minor/major semantiğe göre test edilir. `native_streaming=false` eski versiyonda dürüstçe daha sınırlı sonuç doğurur; yeni UI fallback seçeneğini kullanıcıya bildirir. Protokol aralığı hiç kesişmiyorsa mic capture başlatılmaz.

## 30. Uygulama aşamaları: LIVE0–LIVE12

| Aşama | En küçük teslim | Teknik kabul kapısı |
|---|---|---|
| **LIVE0** | Repo/lockfile, typed contract fixture | Windows build ve schema parse, 001–005. |
| **LIVE1** | Electron main/preload/renderer shell | Strict IPC, CSP, permission handling unit tests. |
| **LIVE2** | Fake sidecar + health + supervisor | Start, handshake, kill, restart, orphan testleri. |
| **LIVE3** | Audio capture/output device adapter | OS permission, 24k transport, hot-swap tests. |
| **LIVE4** | Binary PCM framing + bounded queues | 006–014, overflow/out-of-order controls. |
| **LIVE5** | SessionActor + turn controller | 015–017, lifecycle/idempotency. |
| **LIVE6** | Verified model release loader | 031–034, no unapproved/codec mismatch. |
| **LIVE7** | Speech batch inference + playback | Real mic → model → speaker; 036, 039, true RTF. |
| **LIVE8** | Manual barge-in and stale barrier | 018–023, cancel timeout and queue reset. |
| **LIVE9** | Diagnostics, device/recovery UI | 024–030 and privacy logs. |
| **LIVE10** | Windows installer/update candidate | 040–042, device/protocol smoke. |
| **LIVE11** | Speech native stream integration | Only if Speech's streaming API/cache parity available. |
| **LIVE12** | Optional Agent bridge + full-duplex research gate | Explicit consent, output capability, echo/device tests. |

Bu aşamalar [Live README](../README.md) ve [Live AGENTS](../AGENTS.md) içindeki kilometre taşlarıyla uyumludur; kod reposunda gerçek ilerleme durumu ayrıca tutulur. Belgenin yazılması aşamanın bitmesi değildir. `LIVE7` gerçek kullanıcı sesiyle uçtan uca test edilmedikçe “çalışan speech-native demo” iddiası yapılmaz. `LIVE11` için Speech tarafının upstream API hazır olması gerekir; Live'da fake `stream()` yazarak kapı geçilmez.

### 30.1 PR büyüklüğü ve review kapıları

Her PR tek bir dikey davranış veya testli altyapı dilimi olmalıdır. API şeması değişiyorsa hem producer hem consumer testleri aynı PR/koordineli PR'larda güncellenir. Release manifest parse'ı değiştiren PR Forge Registry contract fixture'ına bakar. Audio device davranışını değiştiren PR yalnız snapshot UI testiyle birleşemez; gerçek/device fixture testleri gerektirir.

## 31. Teslim kanıtı: Codex'in raporu ne içermeli?

Her uygulama çalışması sonunda zorunlu olarak şunlar raporlanır:

1. **Değişen dosyalar:** repo, yol ve neden.
2. **Gerçek statü:** `implemented|experimental|not_implemented`, ayrıca fake/batch/native profili.
3. **Kanıt:** gerçek çalıştırılmış komut, exit code, test sayısı, Windows runner/hardware device bilgisi.
4. **Protocol diff:** schema_version, event enum, PCM header, fixtures, producer/consumer değişimi.
5. **Model release:** model+codec ID, hash verification sonucu, sample rate/codebook metadata.
6. **Audio ölçümü:** TTFA olay tanımı, clock domain, RTF, underrun, sample drop, peak VRAM veya `not_measured`.
7. **Güvenlik:** preload yüzeyi, IPC auth, OS mic permission, log privacy, checksum sonucu.
8. **Failure/recovery:** crash/device/cancel case sonuçları, retry/idempotence.
9. **Kalan blokajlar:** upstream Speech capability, donanım testleri, UI kararı, açık ADR.
10. **Rollback:** neyin güvenle geri alınabildiği ve kullanıcı/model verisinin nasıl korunduğu.

**İş bitirme örneği — kopyalanabilir rapor iskeleti:**

```text
Değişiklik: LIVE5 SessionActor
Statü: Implemented (fake runtime only)
Bildirilen yetenek: native_streaming=false
Çalıştırılan doğrulamalar: [komut, runner, test sonucu]
Geçen fixture'lar: LIVE-ARCH-015,016,017,018 ...
Fiziksel Windows ses testi: NOT RUN — donanım gerektiriyor
Peak VRAM: NOT MEASURED
Güvenlik: renderer yalnız allowlisted command kullanıyor
Rollback: önceki event schema fixture'ına dönüş, veri silme yok
Kalanlar: gerçek Speech batch adapter ve model release
```

Bu iskelet tek başına test sonucu değildir. Uygulayan geliştirici noktalı boşlukları gerçek CI/log kanıtlarıyla değiştirmelidir. Test yapılmadıysa `passed` yazılmaz.

## 32. Açık mimari kararlar ve ADR sahipliği

| Karar | Alternatifler | Son karar için gereken kanıt | Öncelik |
|---|---|---|---|
| Audio device backend | Web Audio, native Node addon, Python native | Windows izin, callback jitter, sandbox, packaging | LIVE3 |
| IPC transport | Auth loopback, pipe, stdio, shared memory | Security + cancel/restart + p95 copy/latency | LIVE2/4 |
| PCM data format | PCM16LE vs float32 | CPU conversion, quality, payload, driver profile | LIVE4 |
| Ring buffer ve chunk | 10/20/40 ms ve 100–300 ms buffers | TTFA, underrun, CPU/p95, interrupt latency | LIVE4 |
| Barge-in | Manual first, later auto VAD/AEC | Echo/false interrupt study | LIVE8/12 |
| Sidecar packaging | Python + wheels vs frozen binary | Clean Windows and AV/installer test | LIVE10 |
| Model release manifest | Kanonik `kaiwen.model.release` | Forge/Speech/Live contract test | LIVE6 |
| Model cache / quantization | FP16, INT8, INT4, CPU fallback | Quality + peak VRAM + RTF on target device | LIVE7/11 |
| Transcript UI | None, optional ASR, generated metadata | Native capability and privacy impact | UX milestone |
| Agent response voice | Learned text conditioning, TTS bridge, text-only | Honest capability, latency, approval and quality | LIVE12 |
| Clock alignment | Same-process instrumentation, sync handshake | Reproducible timing error bounds | LIVE7 |
| Update signing | App signing, release provenance | Tampered update negative cases | LIVE10 |

Açık karar kapatılırken kısa ADR yazılır: bağlam, ölçülen seçenekler, seçimin gerekçesi, reddedilen alternatif ve geri dönüş. “Popüler library” veya “daha profesyonel görünüyor” karar gerekçesi sayılmaz.

## 33. Mimari anti-pattern'ler: kesin yasak listesi

- Renderer'ın tüm mikrofon PCM buffer'ını React state'te tutması; her 20 ms'de setState ile bütün sesin kopyalanması.
- Electron main içine Torch modelinin native extension olarak rastgele gömülmesi ve UI loop'unda blocking inference.
- Ses çalındıktan sonra `generation.cancel` geldi diye eski PCM'nin tekrar kabul edilmesi.
- `turn_id`, `generation_id`, `session_epoch` alanlarını tek sayaç veya tek string ile temsil etmek.
- `native_streaming=true` bayrağının yalnız network audio chunk var diye açılması.
- Binary sesleri base64 JSON içinde mesaj başına şişirip event loop'u kilitlemek.
- Sidecar'ı `0.0.0.0` adresinde authentication'sız açmak.
- Renderer'a genel `fs.readFile`, `shell.exec` veya arbitrary native command API'si vermek.
- Bir `Q/K` codec vocabulary eşleşmesini codec artifact uyumu saymak.
- Forge training checkpoint'ini stable inference release olarak göstermek.
- Windows packaged uygulamasının kaynak kod root path'ine güvenmesi.
- OS mikrofon izni alınmadan playback/mic waveform'u gerçek capture gibi etiketlemek.
- `stop_playback` ile `cancel_agent_task` işlerini tek kontrol anlamı altında birleştirmek.
- CPU fallback'i kullanıcıya haber vermeden GPU performansı diye raporlamak.
- Testte gerçek Speech kullanılmadığı halde “Türkçe speech-native model tamamlandı” demek.
- Veri temizliği için cache klasörü silerken kullanıcı tarafından seçilen model/oturum ayarlarını izinsiz silmek.
- Gerçek cihazdan ölçüm alınmadan “0 ms latency”, “full-duplex hazır” veya “2 GB VRAM garanti” yazmak.

## 34. Definition of Done: mimari başarı ölçütleri

Mimari kodlandı sayılabilmesi için aşağıdaki kanıtlar birlikte aranır:

- [ ] UI yalnız dar preload bridge kullanır; renderer güvenlik izolasyonu kontrol edilir.
- [ ] Sidecar process supervised, authenticated, bounded restart ve temiz shutdown sağlar.
- [ ] Tek session/tur/generation kimlikleri race/idempotence testlerini geçer.
- [ ] PCM format negotiated, header doğrulanmış, queue'lar sınırlı ve telemetrisi mevcuttur.
- [ ] Input sample sırası, kayıp/double paket ve discontinuity semantiği testlidir.
- [ ] Kullanıcı izni ve cihaz açılma sonucu gerçek callback ile doğrulanır.
- [ ] Model release güveni ve codec artifact eşleşmesi yükleme öncesi uygulanır.
- [ ] Gerçek batch mikrofon→Speech→hoparlör zinciri Windows'ta çalışır ve raporlanır.
- [ ] Dört stop operasyonu ayrı ayrı doğru anlamda çalışır; geç gelen ses asla yeniden dinletilmez.
- [ ] Sidecar kill, OOM, device unplug, protocol mismatch ve output underrun testleri vardır.
- [ ] `fake`, `batch_turn`, `chunked_playback`, `native_stream` yetenekleri doğru raporlanır.
- [ ] TTFA/RTF/peak VRAM ölçümleri method, clock ve cihaz bilgileriyle saklanır.
- [ ] OS, installer ve uygulama kapatmada orphan veya açık microphone handle kalmaz.
- [ ] Log ve hata ekranlarında özel ses içeriği veya secret sızıntısı yoktur.
- [ ] Uygun adapter varsa Agent yolu ayrı, opsiyonel ve yetkilidir; yoksa kapalıdır.
- [ ] Bağımlılık, protokol ve model release sürümleri kaydedilip uyumluluk testinden geçer.

Bu listedeki **doküman yazımı** yalnız tasarım kapısıdır. Test/uygulama kutularının işaretlenebilmesi için gerçek kod değişikliği, test raporu ve gerekiyorsa fiziksel cihaz ölçümü gerekir.

## 35. Belgeler arası tutarlılık ve ilerideki iki Live belgesi

- [Live README](../README.md): Ürün amacı, çalışma profilleri, kullanıcı kurulum ve başlangıç sırası.
- [Live AGENTS](../AGENTS.md): Codex için güvenlik, test, davranış, PR ve rapor kuralları.
- [Workspace Overview](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/OVERVIEW.md): Altı depo ekosisteminin vizyonu ve sahipliği.
- [Workspace Integration](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/INTEGRATION.md): Cross-repo manifest/IPC/veri sözleşmeleri.
- [Engineering Standards](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/ENGINEERING_STANDARDS.md): Kod, sürüm, test ve release standartları.
- [Workspace Roadmap](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/ROADMAP.md): Bağımlılıkların sıralanması ve dikey dilimler.
- [Speech Streaming](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/STREAMING.md): Codec ve Transformer'ın gerçek artımlı streaming tasarımı.
- [Speech API](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/API.md): SDK facade, batch/stream arayüzleri ve runtime yetenekleri.
- [Speech Performance](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/PERFORMANCE.md): Gerçek benchmark/VRAM ölçüm sözlüğü ve testleri.
- [Forge Registry](https://github.com/ImtheKaiwen/kaiwen-forge/blob/8bf2af3b925bc1478328b4a26fcba36af74480fb/docs/MODEL_REGISTRY.md): Kanonik yayın, model/codec compatibility, rollback.
- [Forge Evaluation](https://github.com/ImtheKaiwen/kaiwen-forge/blob/8bf2af3b925bc1478328b4a26fcba36af74480fb/docs/EVALUATION.md): Bilimsel model kalite ve değerlendirme kanıtları.
- [Design System](https://github.com/ImtheKaiwen/kaiwen-design): UI component/tasarım sorumluluğu.
- [Agent](https://github.com/ImtheKaiwen/kaiwen-agent): Opsiyonel araç/izin sistemi; entegrasyon çekirdeğe bağlı değil.

`docs/DESIGN_AND_UX.md` mevcut tasarım belgesidir: ilk açılış, mikrofon izinleri, erişilebilir konuşma UI'ı, cihaz ve model seçme, hata mesajları, diagnostic ekranı ve Kaiwen Design bileşenlerini tanımlar. `docs/AGENT_INTEGRATION.md` de mevcut tasarım belgesidir; opsiyonel Agent yetki/görev/sonuç köprüsünü tanımlar. Bu belgelerin mevcut olması UI veya Agent köprüsünün uygulandığı anlamına gelmez. Her ikisi de bu belgedeki IPC, streaming ve mahremiyet sınırlarını değiştirecekse sözleşme ve testleriyle birlikte güncellenir.

## 36. Sonuç ve değişmez mimari taahhüt

Kaiwen Live, Speech modelinin etrafına eklenmiş göstermelik bir chat penceresi değildir. Gerçek zamanlı ses, işletim sistemi donanımı, Python inference, codec/tensör state'i, IPC, kullanıcı izni ve asenkron UI gibi farklı hata alanlarını aynı güvenilir deneyime bağlayan **masaüstü uygulamasıdır**. Bunun başarısı “çok fazla teknoloji kullandık” diye değil; kullanıcı istediğinde mikrofonun açılması, gerçek Türkçe yanıtın üretilmesi, doğru cihazdan duyulması, istenince kesilmesi ve uygulamanın geride izinsiz süreç/ses bırakmadan kapanmasıyla ölçülür.

Geliştirme ilkesi: **önce gözlenebilir ve testli tek dikey dilim; sonra daha iyi kalite/latency; en son otomatik barge-in, Agent ve full-duplex araştırması.** Native streaming yeteneğini Speech upstream doğrulayacak, Live bunu ses cihazı üzerinde end-to-end kanıtlayacaktır. İki repo da birbirinin ölçümüne veya implementasyonuna sahip çıkmadan, açık ve sürümlü interface üzerinden birlikte çalışacaktır.
