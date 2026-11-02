# AGENTS.md — Kaiwen Live: Masaüstü Sesli Asistan Geliştirme Sözleşmesi

> **Belgenin görevi:** Bu repository'de kod değiştiren Codex, başka kodlama ajanları ve mühendisler için uygulanabilir mühendislik kuralları, doğrulama kapıları ve teslim protokolü.  
> **Repository:** `ImtheKaiwen/kaiwen-live`. **Yer:** `kaiwen-ai/kaiwen-live/AGENTS.md`.  
> **İlk hedef:** Windows üzerinde tek kullanıcılı, yerel, Türkçe, mikrofon → Kaiwen Speech → hoparlör **gerçek batch sesli turu**.  
> **Durum:** **HEDEF / GELİŞTİRME TALİMATI**. 30 Ekim 2026 itibarıyla GitHub'daki `kaiwen-live` reposunda yalnız başlangıç `README.md` bulunuyordu. Bu belge kendi başına Electron, Python sidecar, SDK, CI, streaming veya donanım desteğinin geliştirildiğini göstermez.  
> **Kural dili:** **MUST/ZORUNLU**, **SHOULD/ÖNERİLEN**, **MAY/OPSİYONEL**. Bir MUST ihlal edilecekse açık gerekçeli ADR ve test kanıtı gerekir.  
> **Yönetişim:** Mevcut çalışan kod, test çıktısı, gerçek paket sürümü ve sürümlü producer contract; geleceğe dönük bu hedeflerden önceliklidir. Belge kaynak kodu değildir.

---

## 0. Okuma ve talimat önceliği

Kodlama ajanı herhangi bir dosyayı oluşturmadan veya düzenlemeden önce şu bağlamı okumalıdır: [Live README](README.md), [Workspace Integration](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/INTEGRATION.md), [Engineering Standards](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/ENGINEERING_STANDARDS.md), [Speech Streaming](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/STREAMING.md), [Speech API](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/API.md), [Speech Performance](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/PERFORMANCE.md), [Forge Registry](https://github.com/ImtheKaiwen/kaiwen-forge/blob/8bf2af3b925bc1478328b4a26fcba36af74480fb/docs/MODEL_REGISTRY.md). Gereken konularda [Workspace Roadmap](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/ROADMAP.md), [Workspace Overview](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/OVERVIEW.md), [Corpus Export Contract](https://github.com/ImtheKaiwen/kaiwen-corpus/blob/3416d57ce0815af0cb8357c6727cd4ba889bd46d/docs/EXPORT_CONTRACT.md) ve [Forge AGENTS](https://github.com/ImtheKaiwen/kaiwen-forge/blob/8bf2af3b925bc1478328b4a26fcba36af74480fb/AGENTS.md) okunur.

Yetki ve gerçeğin kaynağı sırası: **kullanıcının mevcut görev kapsamı → doğrulanmış çalışan kod/test ve gerçek paket/driver durumu → sürümlü üretici sözleşmesi → bu AGENTS.md → README'deki hedefler → öneri/araştırma notları**. Bu sıra güvenlik gerekliliklerini geçersiz kılmaz. Bir çatışma görüldüğünde gizlice karar verilmez; dosya, sembol, sürüm, etki ve önerilen çözüm raporlanır. Tek taraflı `package.json` değiştirmek veya sahte bir `SpeechEngine` API'sini gerçekmiş gibi import etmek yasaktır.

### 0.1 Uygulama durumunu dürüstçe etiketle

Her özelliğin durumu tek bir doğrulanabilir etikete bağlanır:

| Etiket | Anlamı | İspat |
|---|---|---|
| `not_implemented` | Kaynak kodu bulunmuyor | Repo ağacı ve arama |
| `scaffold` | Arayüz/iskelet mevcut, işlev yok | Kod ve fake işaretleri |
| `simulated` | Fikstür veya sentetik ses | Fake runtime ve fixture kimliği |
| `batch_real` | Gerçek modelle bütün tur inference | Checkpoint, codec, WAV ve test |
| `chunked_transport` | Ses parçalı taşınıyor; model tam tur olabilir | Audio transport test raporu |
| `native_streaming_experimental` | Codec+Transformer gerçek artımlı üretim | Parity, p95 gecikme ve cihaz kayıtları |
| `validated` | Tanımlı donanım, sürüm ve test matrisi geçti | Ölçüm ve release kanıtı |

Bir UI animasyonu, VAD kararı, ASR transcript'i, fake `pcm_chunk` veya başarılı HTTP health isteği `native_streaming_experimental` kanıtı değildir. Agent hiçbir zaman bir modu sessizce daha yüksek statüyle göstermez. `batch_real` semantik olarak iyi yanıt verdiğinin değil, gerçekten model çalıştırıldığının kanıtıdır.

### 0.2 Repo ve çalışma alanı gerçeği

`kaiwen-ai/` yerel koordinasyon dizinidir; kendisi yedinci Git reposu değildir. `kaiwen-live` kendi lockfile, test, release, CI ve bağımlılık sınırına sahip bağımsız repodur. Diğer beş repo sibling'dir. Kullanıcının açık isteği olmadan `git push`, force push, branch silme, GitHub release, model indirme, büyük dataset transferi veya Windows installer yayınlama yapılmaz. Sadece belge yazımı istendiğinde uygulama kaynak kodu değiştirilmez.

## 1. Görev başlamadan önce zorunlu keşif

Ajan işe **en küçük doğrulanabilir görev** ile başlar; aşağıdaki sırayı izler:

1. `git status --short`, mevcut branch ve commit hash'i kaydet; kullanıcının önceden yaptığı değişiklikleri koru.
2. Repo ağacını incele; gerçek kaynak kodu, mevcut testleri, CI ve paketleme dosyalarını doğrula.
3. İlgili `AGENTS.md`, README ve mimari sözleşmelerini oku; belge var diye özellik var sayma.
4. `kaiwen-speech` gerçek Python import kökünü ve checkpoint API'sini incele; `kaiwen_voice` ile repo adı `kaiwen-speech` aynı şey değildir.
5. Windows, Python, Node, Electron, cihaz/driver, FFmpeg ve paket yöneticisi sürümlerini uygun şekilde kaydet.
6. Kullanıcının verdiği gereksinimi test edilebilir bir kabul cümlesine dönüştür; kapsam dışı işleri belirt.
7. Etkilenecek producer/consumer sözleşmelerini ve geriye uyumluluk risklerini listele.
8. Yeni bağımlılık eklemeden önce neden mevcut araçla çözülmediğini yaz; lisans, boyut ve supply-chain etkisini ölç.
9. En az bir başarısızlık/iptal testini, en az bir başarılı senaryoyu ve geri dönüş yolunu tanımla.
10. Ancak sonra kodu küçük, gözden geçirilebilir bir dikey dilim olarak değiştir.

Daha önce yapılmış bir keşif varsa doğrulanabilir commit/revizyonuna atıf yapılabilir; yeni durumda eski varsayımlar kopyalanmaz. Bütün repo için `rm -rf`, otomatik "cleanup" veya şüpheli migration yapılmaz. Değişiklik öncesi korunacak kullanıcı verileri açıkça belirlenir.

### 1.1 İlk çalıştırılabilir teslimin sınırı

`LIVE0` için depo altyapısı, TypeScript/Python tip kontrolü, güvenli Electron shell, minimum test fixture, CI ve README'de **gerçek komutlar** yeterlidir. `LIVE1–LIVE2`'de model değil, gerçek mikrofon ve hoparlör loopback'i kanıtlanır. `LIVE3` fake sidecar ve session sözleşmesini sınar. `LIVE4` gerçek Speech batch inference'ını uçtan uca ekler. Çoklu tenant, canlı telefon çağrısı, sosyal ağ, kayıt toplama platformu, kalıcı bulut oturumu veya GPU cluster bu işlerin kapsamına alınmaz.

## 2. Repository sahipliği ve bağımlılık yönleri

| Proje | Sahibi olduğu iş | Live'ın yapabileceği | Live'da yasak olan |
|---|---|---|---|
| **Live** | Windows UI, mikrofon, hoparlör, yerel sidecar supervisor, audio queue, playback, session, kullanıcı onayı | Adapter ve typed protocol | Model mimarisi veya eğitim loss'u yazmak |
| **Speech** | Codec, Transformer, batch/incremental inference ve Python SDK | Sürümlü public SDK tüketmek | Electron/OS audio iznini Speech'e taşımak |
| **Forge** | Eğitim orkestrasyonu, model değerlendirmesi, registry, yayın manifesti | Release doğrulayıp kurmak | Training checkpoint'ini kendiliğinden stable ilan etmek |
| **Corpus** | Ses toplama, izin, etiket, dataset export | Gerekirse test fixture kaynağını tanımak | Dataset hazırlama modülü veya crawler yapmak |
| **Design** | Ortak React/TS bileşenleri ve design token | Mevcut paketi sürüm sabitleyerek kullanmak | Ayrı bir komponent kütüphanesini kopyalamak |
| **Agent** | Tool policy, workflow, onay, bilgi toplama | İzinli adapter ile çağrı yapmak | Araçları renderer'a veya Speech tokenlarının içine gizlemek |

Ajan, Live içindeki `adapters/speech` katmanının `kaiwen_voice` fonksiyonlarını sarabilmesini sağlayabilir; ancak `src/kaiwen_voice` kopyası oluşturmaz. `Forge` sürümlü artifact metadata'sını güven sözleşmesi olarak sunar; Live onu yeniden üretmez. `Agent` ayakta değilken temel sesli görüşme devam edebilmelidir. UI component'ı Live'a özgü ise burada, genel amaçlı ise gerekli doğrulamayla Design'da geliştirilir.

### 2.1 Geri dönüş sözleşmesi

Başka repoda yeni API gerektiğinde: consumer ihtiyacını ve expected contract fixture'ını yaz; ilgili repo değişikliğini ayrı PR olarak öner; producer sürümü oluşmadan Live'a geçici sahte import ekleme. Geçiş için feature negotiation ve backward-compatible adapter kullan. Altı repoyu tek commit veya tek lockfile haline getirme.

## 3. Hedef kod organizasyonu ve dizin disiplini

Aşağıdaki yapı **hedef öneridir**, mevcut `kaiwen-live` repo ağacı değildir. İhtiyaç doğduğunda mümkün olan en küçük parça açılır:

```text
kaiwen-live/
├── README.md
├── AGENTS.md
├── package.json                         # HEDEF: Electron / React / TypeScript
├── package-lock.json                    # HEDEF: Seçilen paket yöneticisinin lockfile'ı
├── apps/
│   ├── desktop/
│   │   ├── electron/
│   │   │   ├── main/                    # Window, supervisor, updater
│   │   │   ├── preload/                 # Dar, şema doğrulamalı IPC köprüsü
│   │   │   └── audio/                   # OS input/output / native bridge
│   │   └── src/
│   │       ├── features/                # Session, models, devices, settings
│   │       ├── components/              # Live'a özgü UI
│   │       └── state/                   # Tipli durum adaptörleri
│   └── sidecar/
│       ├── pyproject.toml
│       └── kaiwen_live_sidecar/         # Speech adapter, transport, health
├── packages/
│   └── protocol/                        # Kontrol mesajı şemaları ve sürüm
├── tests/
│   ├── contract/
│   ├── integration/
│   └── audio-fixtures/
├── docs/
│   ├── ARCHITECTURE.md                  # Mevcut tasarım belgesi; uygulama planlanıyor
│   ├── DESIGN_AND_UX.md                 # Mevcut tasarım belgesi; uygulama planlanıyor
│   └── AGENT_INTEGRATION.md             # Mevcut tasarım belgesi; Agent köprüsü planlanıyor
└── .github/workflows/                   # Başlangıç kalite kapıları
```

**Dizin isimleri kanun değil, sahiplik ve şema sınırları kanundur.** Örneğin `pnpm` tercih edilirse `package-lock.json` yerine `pnpm-lock.yaml` saklanır ve tek paket yöneticisi kullanılır; iki lockfile birlikte oluşturulmaz. Başka bir framework yalnız kullanıcı ve testlerle gerekçelendiriliyorsa değerlendirilir. Boş placeholder dosyaları üretme; her eklenen modülün gerçek asgari işlevi ve testi olmalıdır.

### 3.1 Dosya ve modül kuralları

Her modülün bir açık sorumluluğu, minimum public yüzeyi ve test edilebilir sınırı olur. Audio device manager ile session reducer aynı devasa `main.ts` içine gömülmez; renderer'dan codec yüklenmez. Ses dosyaları ve test WAV'ları kaynak repoya büyük binary olarak kazara commit edilmez; küçük, lisanslı fixture'lar istisnadır. Backend venv, model ağırlıkları, trace ve gerçek kullanıcı kayıtları `.gitignore` içinde tutulur. Paketlemeye giren asset listesi her release'de gözden geçirilir. Dizin taşımalarında import, Windows packaged path, `.asar` ve main/preload çözücüleri uyumlu değiştirilir.

## 4. TypeScript, React ve Electron kod kalitesi

- TypeScript `strict` açılır; uygulama sınırında `any` yerine doğrulanan `unknown` kullanılır.
- Kullanıcı aksiyonları, cihaz olayları, model olayları ve IPC mesajları ayrık union tiplerle modellenir.
- Side effect'ler renderer event handler'ına dağılmaz; session controller ve state reducer arasında net sınır olur.
- React bileşenleri Electron API'sini her yerde doğrudan çağırmaz; UI fake desktop adapter ile test edilebilir.
- Her event subscription `unsubscribe` döndürür; component unmount'unda temizlenir. Çift listener leak yasaktır.
- Asenkron yarış ve stale state için `session_epoch` ve `generation_id` eşleşmeyen sonuç gösterilmez.
- UI donanım durumunu gerçek adapter sinyaliyle gösterir; geçici spinner başarının kanıtı değildir.
- `kaiwen-design` paketinin gerçek npm adı/ithal yolu kurulum sırasında kontrol edilir; hayali import kullanma.
- Dark/light tema, monokrom tipografi, reduced motion ve erişilebilir odak Design üzerinden sağlanır.
- Test dışı `console.log` ile konuşma metni, PCM, model mutlak yolu, secret veya token basılmaz.

### 4.1 Electron main / preload / renderer sınırları

**Main**, pencere ve sidecar supervisor, model kurulumu, sınırlı işletim sistemi işlemleri ve ses cihazı servisinin yetkili katmanıdır. **Preload**, `contextBridge` ile yalnız izinli, şema doğrulanan çağrıları expose eder. **Renderer**, güvenilmez görünüm kodu gibi ele alınır; serbest Node erişimi, `spawn`, `fs`, `child_process`, raw IPC kanalı veya keyfi disk yolu verilmez.

1. `nodeIntegration: false` ve `contextIsolation: true` zorunludur; `sandbox: true` mümkün olan ilk sürümde etkin olmalıdır. Engel varsa ADR ve azaltıcı önlem gerekir.
2. `webSecurity` kapatılmaz; uzaktan HTTP içerik Electron'da keyfi açılmaz. Navigation, external link ve `shell.openExternal` için allowlist kullan.
3. Content Security Policy geliştirme ve packaged ortamda ayrı doğrulanır; `unsafe-eval` üretime taşınmaz.
4. IPC handler, sender frame/origin/yetkili pencere ilişkisini kontrol eder; renderer yalnız ID bildiği için başka oturumu yönetemez.
5. Preload sadece `AudioDevice`, `SpeechSession`, `ModelLibrary` gibi dar metotlar expose eder; `executeCommand`, `readAnyFile`, `downloadUrl` gibi yetki yoktur.
6. IPC girişinde string boyutu, ID, enum, süre, sayısal aralık ve payload byte limiti runtime'da doğrulanır. TS tipi runtime validation değildir.
7. Main → renderer event'leri bounded subscription ve payload boyutu sınırına tabidir; UI kapalıyken heap birikmez.
8. Native modül kurulursa güvenilir build, Windows mimari/ABI uyumu, sandbox ve imzalama değerlendirilir; `--no-sandbox` kolaycılık olarak kullanılmaz.

### 4.2 Dar preload sözleşmesi — HEDEF

```typescript
// HEDEF / NOT IMPLEMENTED — çalışan kod değildir.
type SessionId = string;
type GenerationId = string;

interface LiveDesktopBridge {
  listAudioDevices(): Promise<{ inputs: string[]; outputs: string[] }>;
  requestMicrophonePermission(): Promise<"granted" | "denied" | "unavailable">;
  openSession(): Promise<{ sessionId: SessionId; sessionEpoch: number }>;
  endTurn(sessionId: SessionId): Promise<void>;
  stopPlayback(sessionId: SessionId): Promise<void>;
  cancelGeneration(sessionId: SessionId, generationId: GenerationId): Promise<void>;
  closeSession(sessionId: SessionId): Promise<void>;
  onSessionEvent(listener: (message: unknown) => void): () => void;
}
```

Bu metotlar Live adapter hedefidir; Speech Python SDK'sında bugün mevcut oldukları iddia edilmez. Gerçek implementasyon geldiğinde tek sürümlü protokol şemasından TypeScript/Python contract fixture üretmek tercih edilir. IPC request ID ve authorization, metoda özgü olur; 'gönderildi' ile 'uygulandı' ACK'i karıştırılmaz.

## 5. Python sidecar ve Speech adapter kuralları

Sidecar ayrı process olarak tek bir yetkili `Speech` model yükleyicisine sahip olmalıdır. Python içinde model katmanları, trainer, ASR→LLM→TTS pipeline veya codec fonksiyonları kopyalanmaz. Halihazırda Speech dağıtım adı **`kaiwen-voice`**, import kökü **`kaiwen_voice`**'tir. `KaiwenSpeechTransformer`, `MimiCodec`, `load_checkpoint`, `build_dialogue_prompt` ve `generate` mevcuttur; `SpeechEngine` ve gerçek `stream_session` ise hedef API'dir.

### 5.1 Gerçek baseline ile ilk bağlantı

```python
# MEVCUT SPEECH API — uyumlu güvenilir checkpoint ve audio bağımlılıkları
# gerektirir. Live sidecar henüz geliştirilmemiştir.
from kaiwen_voice.training.checkpoint import load_checkpoint
from kaiwen_voice.codec.mimi_codec import MimiCodec
from kaiwen_voice.inference.generate import build_dialogue_prompt, generate

model, step, _payload = load_checkpoint("/trusted/releases/model.pt", device="cpu")
model.eval()
codec = MimiCodec.from_pretrained(
    "kyutai/mimi", num_codebooks=model.config.num_codebooks, device="cpu"
)
# user_audio yükleme, encode, prompt, generate, decode ve playback işlemleri
# Live adapter içinde ayrıca geliştirilir ve tek tek doğrulanır.
```

`MimiCodec.from_pretrained` ilk kullanımda ağdan model indirebilir; ilk model edinme için açık kullanıcı adımı, cache/izin ve dosya bütünlüğü gerekir. Model/codec için `codebook_size`, `num_codebooks`, token sözlüğü, frame/sample rate, sürüm/hash ve acoustic delay uyumu doğrulanmalıdır; yalnız kod kitabı sayısı eşitliği yeterli değildir. Örnek, ses kalitesi veya streaming garantisi değildir. `.pt` yüklerken PyTorch `weights_only=True` kullanımı tek başına tüm tedarik zinciri saldırılarını önlemez; dosya kaynağı ve hash kontrolü ön koşuldur.

### 5.2 Sidecar yaşam döngüsü

Normal açılış `not_running → starting → transport_ready → loading_model → model_ready → session_ready` geçişini izler. Hata durumu `starting | loading_model → failed → retryable_or_fatal`, kapanış `closing → closed` olur. `transport_ready` yalnız iletişim kanalının açık olduğunu gösterir; modelin yüklendiğini göstermez. `model_ready` için gerçek model+codec yükleme ve uyumluluk doğrulaması gerekir. Audio smoke geçilmeden `validated_audio` raporlanmaz.

Aşağıdaki event örneği yalnız tasarımdır ve gerçek session'a bağlanan, modelin fiilen yüklendiği durum için geçerlidir:

```json
{
  "protocol_name": "kaiwen.live.session",
  "protocol_version": "1.0.0",
  "event_id": "evt_model_ready_01",
  "session_id": "session_example_01",
  "stream_id": "stream_example_01",
  "sequence": 3,
  "event_type": "model_ready",
  "occurred_at_utc": "2026-10-30T12:00:00Z",
  "monotonic_ns": 100000000,
  "correlation_id": "corr_demo_01",
  "payload": {
    "mode": "batch_real",
    "model_id": "model_example",
    "codec_id": "mimi_reference",
    "features": ["batch_inference"]
  }
}
```

Henüz session açılmadan gelen servis durumu için ayrı `system_event` sözleşmesi kullanılması gerekebilir; sahte `session_id` üretip gerçek protokole yollama. Event ID ve sequence tekrar korumalı ve artan olmalıdır. Handshake öncesi audio kabul edilmez.

### 5.3 Process sahipliği ve cleanup

Electron main sidecar'ı sabit, doğrulanmış exe/komut ve argument dizisiyle başlatır; `shell=true` kullanmaz. PID, child handle, pipe/port ve kaynakların tek sahibi supervisor'dır. stdout/stderr bounded ve redacted log'a dönüştürülür. Kapanış: yeni capture durdur → aktif generation cancel → playback boşalt → session close → sidecar graceful stop → timeout sonrası gerektiğinde process tree terminate. CUDA, device handle ve memory'nin process çıkışından sonra gerçekten serbest kaldığı doğrulanır. Sidecar çökünce UI beyaz ekran olmamalı; oturum `failed` olur, cihaz güvenle bırakılır ve kullanıcı açık retry seçeneği görür.

### 5.4 Restart storm önleme

Arka arkaya crash sonrası sonsuz hızlı yeniden başlatma döngüsü yasaktır. Sınırlı deneme, exponential backoff ve elle yeniden deneme vardır. GPU OOM ile şema parsing hatası aynı retry politikasını almaz. Bozuk model tekrar tekrar otomatik yüklenmez; kullanıcıya güvenli model seçim ekranı açılır. Önceki session nesli kapatılır; eski IPC yanıtları yeni instance'a taşınmaz.

## 6. Ses cihazı, capture ve playback sahipliği

Gerçek mikrofon ve hoparlör **Live** tarafından OS/audio driver bağlamında açılır. Speech model katmanı OS microphone API'si çağırmaz. İlk milestone gerçek cihaz loopback'idir; model sonraki aşamadır. Capture ve playback lifecycle'ı ayrı yönetilir; biri hata verdiğinde diğerindeki durum anlaşılır olmalıdır.

### 6.1 Gerçek zamanlı audio callback yasakları

Callback içinde hiçbir koşulda GPU inference, codec model yükleme, disk I/O, senkron network, renderer'a yüksek frekanslı event flood, uzun lock, büyük tensor allocation veya blocking Python FFI yapılmaz. Callback en fazla timestamp/sample index kaydeder, bounded buffer push/pop yapar, sayaç artırır ve beklemeden çıkar. Ağır hesaplama worker üzerinden yürür. Deadlock yaratmayan bounded wait/lock-free tasarım platform testleriyle doğrulanır.

### 6.2 Format ve frame hesabı

Her audio boundary en az `sample_rate_hz`, `channels`, `sample_format`, `frames_per_chunk`, `sample_index`, `sequence`, `clock_domain`, channel layout ve endian bilgisine sahiptir. PCM16 ve float32 aynı bytes değildir. OS 48 kHz mikrofonu codec'in 24 kHz desteklediği anlamına gelmez; sample-rate conversion callback dışında, kalite ölçümlü uygulanır.

**Somut hesap:** 24 kHz sesin 20 ms'lik mono PCM16 paketi `24_000 × 0,020 = 480` sample ve `480 × 2 = 960` byte'tır. 48 kHz cihazda aynı 20 ms `960` sample'dır. Codec frame rate (Mimi 12,5 Hz) ses taşıma paket oranıyla karıştırılmaz. Chunk `duration_samples` ve sample index tamsayıdır; kayan noktalı milisaniye birikimiyle ses konumu hesaplanmaz.

### 6.3 İzin ve cihaz değişimi

Mikrofon izni reddedilirse `permission_denied` UI ve OS yönergesi gösterilir; sahte waveform ile 'dinleniyor' denmez. Default mic değişince active device validity yeniden kontrol edilir; yakalama güvenle durur veya yeniden negotiation olur. `mic_muted`, `device_missing`, `capture_paused` ve `model_not_ready` farklı durumlardır. Kullanıcı mikrofonu kapatınca capture handle ve yeni paket sayacı gerçekten durur; UI'da göstergenin kapanması tek başına yeterli değildir.

### 6.4 Echo ve yanlış barge-in

Hoparlörde üretilen sesin mikrofona dönmesi yanlış VAD/interrupt kararı verebilir. Gerçek AEC yoksa full-duplex barge-in çalışıyor iddiası yapılmaz. İlk sürümde manuel kesme kontrolü kabul edilebilir. Otomatik kesme için ayrı kulaklık/açık hoparlör, farklı ses düzeyi, sessiz ortam ve gürültülü ortam testleri yapılmalıdır. Kendi kendine tekrar yanıt üreten feedback döngüsü release blocker'dır.

## 7. Session / turn / generation kimlikleri ve state machine

`session_id` kullanıcının konuşma oturumunu, `turn_id` bir kullanıcı konuşma turunu, `generation_id` modelin yanıt üretim denemesini, `stream_id` belirli ses akışını, `session_epoch` ise yeniden oluşturma/iptal sonrası eski olayları dışlamak için kullanılan nesil sayacını temsil eder. Bu alanlar birbirinin yerine kullanılamaz. Aynı turn için generation retry yeni `generation_id` oluşturabilir.

### 7.1 İzinli durum geçişleri

Kanonik üst düzey durumlar: `created → initializing → ready → listening → processing → speaking → ready`; terminalde `closing → closed`, hata yolunda `failed`. Her mod aynı geçişten geçmek zorunda değildir; batch/streaming capability'ye göre izinli geçiş tablosu testlidir. `speaking`, yalnız model PCM ürettiği için değil cihaz gerçekten ses yürütmeye başladığında kullanıcıya gösterilir.

- `open_session` idempotency anahtarı varsa aynı oturumu döndürür; çift model işi açılmaz.
- `begin_turn` yalnız geçerli session/capture durumunda kabul edilir; aktif turn iki kere açılmaz.
- `submit_pcm` eski epoch veya kapalı turn için reddedilir; aşırı paketler sınırsız RAM'e yığılmaz.
- `end_turn` girişin kapandığını işaretler; daha önce kuyrukta alınan PCM işlenmeden üretim başlamaz.
- `cancel_generation` yalnız ilgili aktif generation için idempotent davranır; başkasının turunu durdurmaz.
- `close_session` tekrar çağrıldığında cihaz ve model kaynaklarını ikinci kez serbest bırakmaya çalışıp çökmez.

### 7.2 Stale event ve sıra dışı mesajlar

`session_epoch`, `generation_id` veya `stream_id` eşleşmeyen PCM çıktısı **çalınmaz**. İptalden sonra gecikmiş çıktı `audio_output_rejected_stale` sayılır; yeni yanıt gibi görünmez. Aynı `sequence` tekrar gelirse duplicate politikası, eksikse gap politikası uygulanır. IPC yerel olduğu için race yoktur varsayımı yanlıştır. Producer reset sonrası eski stream ID'sini yeniden kullanma. Listener unsubscribe olduğunda event flow başka penceredeki kullanıcıya yönlenmez.

### 7.3 Bağlam ve geçmiş sınırları

Oturum geçmişi GPU bellek ve token context üzerinde sınırlandırılır. Her turn'ü sonsuza kadar model girdisine eklemek düşük VRAM hedefiyle çelişir. V1'de tek tur kabul edilebilir. Çoklu turn context semantiği, konuşmacı kimliği, önceki ses tokenlarının saklanması ve kişisel veri retention ayrı tasarım gerektirir. Sohbet silme, yalnız UI listesini değil varsa cache, temp WAV ve kalıcı transkriptleri de ele alır.

## 8. Dört durdurma işlemi birbirinin yerine kullanılamaz

| Komut | Asıl etki | Tek başına garanti etmediği şey | Kabul kanıtı |
|---|---|---|---|
| `stop_playback` | Çıkış ses tamponunu boşaltıp sesi susturur | GPU generation'ın durması | Eski PCM bir daha duyulmaz |
| `cancel_generation` | Belirli generation işini iptal eder | Mikrofonun kapanması ve önceden queue'da sesin temizlenmesi | Yeni PCM gelmez veya stale diye reddedilir |
| `stop_microphone` | Yeni capture paketlerini durdurur | Üretim ve playback'in durması | OS mic handle ve capture counter durur |
| `close_session` | Oturumun bütün kaynaklarını kapatır | Her platformda sıfır süreli teardown | Handle/process/queue cleanup geçer |

Barge-in sırasında `stop_playback + cancel_generation + stale epoch invalidation` birlikte koordine edilir. Audio callback içinde generation cancel için bloklayan kod çalışmaz; ayrı control queue sinyal verir. ACK tipinin **request accepted** mı **operation completed** mı olduğu sürümlü sözleşmede açık olur. ACK gelmediğinde UI success göstermez; timeout ve cleanup uygulanır. Stop playback sessizliği üretirken modelin arka planda GPU tüketiyor olması raporda açıkça yakalanmalıdır.

### 8.1 Kesme ve yeniden konuşma yarışı

Şu senaryo ayrı test edilir: `gen-01` ses üretirken kullanıcı durdur düğmesine basar; aynı anda `gen-01` eski PCM packet'i IPC'den gelir; kullanıcı yeni `turn-02` başlatır ve `gen-02` oluşturulur. Eski PCM hoparlöre asla yazılmaz. `session_epoch` arttırıldıktan sonra eski ACK/ERROR yeni state'i değiştiremez. İptal sonrası device buffer'ında kalan sesin sayısı ölçülür; yalnız UI durumuna bakarak işlem tamamlandı sayılmaz. Bekleyen chunks kime ait olduğu bilinmeden ortak global queue'da tutulamaz.

## 9. Fake, batch, chunked transport ve native streaming ayrımı

Bu dört düzey teknik olarak farklıdır ve hiçbir isimlendirme hilesiyle bir üst düzeye çıkarılamaz:

- **Fake:** Bilinen fixture sesi veya sentetik dalga; model inference yok; UI `Simulated Audio` gösterir.
- **Batch:** Kullanıcı turn'ü kapanır; bütün input codec'e girer, bütün output üretilir ve ardından ses çalınır.
- **Chunked transport:** Önceden hazırlanmış çıktı PCM parçalarına bölünüp taşınır; modelin artımlı üretim yaptığı kanıtı değildir.
- **Native streaming:** Codec state ve Transformer KV cache/RoPE pozisyonları gerçek artımlı çalışır; decoder artımlı ses üretir, bounded buffer çalar.

`kaiwen_voice.inference.generate` mevcut halde full prefix yeniden hesaplar. Ajan yalnızca WAV'i küçük parçalara ayırdı diye “native streaming tamamlandı” raporlayamaz. Speech'e özgü KV cache kodu Live'a yazılmaz; producer Speech reposunda geliştirilir. Cached model sonucu ile batch sonucu uygun tolerans ve örneklerde karşılaştırılmadan parity ilan edilmez.

### 9.1 PCM chunk metadata ve transport

Her ses chunk'ında en az `session_id`, `turn_id`, `generation_id`, `stream_id`, `session_epoch`, `sequence`, `sample_index`, `sample_rate_hz`, `channels`, `sample_format`, `payload_byte_length` ve `is_final` anlamı bulunur. Control plane küçük JSON mesajları taşır; sürekli PCM için bounded binary taşıma tercih edilir. Büyük PCM blob'larını JSON/base64 yapıp yüksek frekansta renderer'a gönderme. Named pipe, authenticated loopback ve shared memory seçenekleri erişim kontrolü, cleanup, timing ve packaging testine göre seçilir. `sequence` her stream'de sıfırdan başlayabilir; cross-stream monotonik global ID sanılmamalıdır.

### 9.2 Backpressure, underrun ve gözlemlenebilirlik

Capture, inference ve playback kuyrukları ayrı limitlere sahip olmalıdır. Kuyruk dolunca RAM şişirme veya bütün iş parçalarını bekleterek deadlock oluşturma. Capture için tanımlı drop/error; inference için bounded timeout; playback için eski generation paketlerinin atılması ve underrun sayaçları bulunur. `queue_depth`, `queue_wait_ms`, `dropped_input_samples`, `output_underruns`, `stale_chunks` ve cancellation süresi ölçülür. Bir hata concealment ile saklandıysa ölçümde açıkça görünür. Drop edilen input'un sample index'i, sonraki paketlerin ses zamanlarını uydurarak değiştirmez.

### 9.3 Clock domain ve TTFA

Ayrı olaylar: `turn_end_detected`, `first_generated_token`, `first_decoded_pcm`, `first_pcm_enqueued`, `first_pcm_played_device`. Gerçek kullanıcıya duyulan ses gecikmesini `first_token_ms` diye gösterme. Sidecar monotonic ve OS audio device clock'ları doğrudan çıkarılıp gecikme bulunmaz; kalibrasyon veya aynı clock domain gerekir. `p50`, `p95`, `p99`, test `n`, cihaz ve ses uzunlukları rapora yazılır.

## 10. Protocol, handshake ve capability negotiation

Cross-repo hedef protokol adı `kaiwen.live.session`, başlangıç önerilen sürüm `1.0.0`'dır. Gerçek repo sürümleri kurulum sırasında doğrulanmalıdır. Schema değişikliği yalnız Live tarafında yapılmaz; producer/consumer fixture ve migration birlikte güncellenir. Desteklenmeyen özelliğe otomatik true fallback yapılmaz.

### 10.1 Örnek capability response — HEDEF

```json
{
  "protocol_name": "kaiwen.live.session",
  "protocol_version": "1.0.0",
  "runtime_mode": "batch_real",
  "capabilities": {
    "batch_inference": true,
    "chunked_playback": false,
    "native_streaming": false,
    "barge_in_auto": false,
    "barge_in_manual": true,
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

Bu JSON örneği **hedef protokol fikstürüdür**; gerçek bir servisten okunmuş yanıt değildir. `barge_in_manual` kullanıcının durdurma kontrolüdür, full-duplex desteği kanıtı değildir. `native_streaming=false` ise UI native streaming etiketi açılmaz. Client ve sidecar, desteklenen protocol major, audio format ve model release capability kesişimini handshake sırasında hesaplar. Desteklenmeyen version sistem kaynaklarını gereksiz açmadan güvenle reddedilir.

### 10.2 Hata, sürümleme ve eski client

Wire error şemasında `code`, `message`, `retryable`, `context`, `correlation_id` gibi alanlar sürümlenir. Renderer'a stack trace, dosya içeriği, username içeren path, auth secret veya speech text dökülmez. Unknown enum güvenli `unsupported` olur. IPC değişiminde schema snapshot testi, producer contract testi ve consumer contract testi gerekir. Major değişim SemVer migration şartı doğurur; alias ile sessiz uyumluluk uydurulmaz.

## 11. Model release güveni, codec kimliği ve rollback

Forge Registry release manifest, hash, lisans ve değerlendirme/onay politikalarının sahibidir. Live sadece **doğrulanmış inference release** tüketir; training checkpoint'i kendiliğinden stable değildir. `num_codebooks`, `codebook_size` eşleşmesi yetmez; codec adı, gerçek weight/quantizer hash, frame/sample rate, token kontrol ID'leri, acoustic delay ve model konfigürasyonu birlikte doğrulanır. Uyumsuz paket yüklenmeden açık hata verilir.

### 11.1 Model edinme ve etkinleştirme sırası

1. Manifesti kullanıcı seçimi veya güvenilir release kanalından edin.
2. Yayıncı trust root, lisans/dağıtım izni, kanal ve uygulama uyumluluğunu doğrula.
3. İndirme boyutu, disk alanı, user consent ve veri egress'i kontrol et.
4. Dosyaları staging dizinine aktar; yarım dosyayı aktif release gibi gösterme.
5. SHA-256 ve boyut kontrolünü **yüklemeden önce** yap.
6. Archive path traversal, symlink escape, ZIP bomb ve unsupported payload tiplerini reddet.
7. Codec ve model metadata'sını istenen runtime'da doğrula.
8. Gerçek model readiness smoke koşusu yap; başarıyı sınırlarıyla kaydet.
9. Aktif oturumun state'ini bozmadan sonraki session'da yeni sürümü etkinleştir.
10. Hata varsa önceki **doğrulanmış ve uyumlu** release'e rollback yap.

SHA-256 beklenen bytes ile eşitliği kanıtlar; yayıncının güvenilirliğini tek başına kanıtlamaz. Manifestin güven kökü/imza mekanizması ayrıca uygulanır. Keyfi URL, `localhost` veya internal IP'leri tarama aracına dönüşemez. Modelin kullanıcı onayı olmadan birkaç GB indirilmesi yasaktır.

### 11.2 Release manifest adı uyuşmazlığı

Önceki taslaklarda `kaiwen.model.release` ve `kaiwen.speech.release` biçimleri bulunabilir. Forge Registry belgesi `kaiwen.model.release` kanonik sözleşmesini öneriyor. Bunun gerçek koda ve diğer belgelere migrasyonu ayrı producer–consumer contract işi olarak takip edilmelidir; yeni bir alias yazıp her iki formatı sessizce uyumlu varsayma. Migration gerçekleşmediyse Live kurulumunda sürüm uyumsuzluğu açıkça bildirilir.

### 11.3 OOM ve düşük VRAM

GPU OOM olduğunda aynı modeli sonsuz retry etme; sessiz cloud fallback yapma. Runtime destekliyorsa ve kullanıcı kabul ediyorsa ölçümlü CPU fallback veya daha hafif model seçimi sunulabilir. **2 GB VRAM cihaz desteği araştırma hedefidir**, ürün garantisi değil. Toplam bellek hesaplaması yalnız model weights ve PyTorch allocated değil, codec, allocator reserved, CUDA runtime, playback/capture buffer ve diğer bellek kullanımını içerir.

## 12. Fake/test fixture ile gerçek sesin sınırı

Fake sidecar deterministik PCM ile UI, event sırası, state transition, cancellation ve retry testini destekler. Demo açıkça `Simulated Audio` etiketlidir. Fake test pass'i gerçek hardware, gerçek model semantiği veya konuşma kalitesi pass'i değildir. Test fixture'ları kısa, açık izinli Türkçe konuşmalardan veya sentetik dalgalardan oluşur; kaynak lisansı, süre, sample rate, kanal, beklenen hash ve kullanım amacı belirtilir.

### 12.1 Doğrulamanın üç seviyesi

1. **Unit/fake:** donanım gerektirmeyen deterministic state, queue, IPC ve timeout testleri.
2. **Gerçek Speech integration:** uyumlu checkpoint ve codec ile gerçek WAV→WAV; output süresi ve codec formatı ölçülür.
3. **Hardware/manual:** OS mikrofonundan gerçek sample capture, hoparlörden gerçekten duyulan ses, cihaz değişimi ve kapatma testi.

Bu üç seviyeyi raporda ayrı göster. Gerçek donanım yoksa `NOT_RUN_NO_DEVICE` yaz; mock mic PCM sample sayısını fiziksel mikrofon testi diye anlatma. Kişisel konuşma kayıtlarını test fixture'a kopyalama; izinli örnek kullan.

## 13. Mahremiyet ve local-first çalışma

Ses içeriği hassas kullanıcı girdisidir. Mikrofon yalnız açık kullanıcı eylemi ile açılır; başlangıçta otomatik dinleme veya wake word bulunmaz. Kullanıcının sesi, transkripti ve Agent çıktıları varsayılan kalıcı kaydedilmez. Crash log, analytics ve diagnostik export ham PCM içermemelidir.

- Session bitince bounded PCM ring buffer temizlenir, temp WAV gerekiyorsa uygulama kontrollü dizinden güvenle silinir.
- Log'a yalnız asgari sayısal metrikler, anonim oturum kimliği ve hata kodları girer; konuşulan metin girmez.
- `delete conversation`, varsa ses/cache/transcript/türev artifact'ları da kapsar; yapılmayan silme kullanıcıya açık söylenir.
- Modelin ilk indirilmesi çevrimdışı konuşmadan ayrı izinli bir ağ eylemidir.
- Agent dış ağa veri gönderecekse kullanıcıya açık onay, domain ve payload kapsamı belirtilir.
- Debug flag, secret ve kişisel içerik loglamayı otomatik açmaz.
- Diagnostik paylaşım isteğe bağlı ve redacted olmalıdır; storage retention belgelenir.

### 13.1 Lokal servis tehdit modeli

Localhost portu kullanılıyorsa sadece `127.0.0.1`'e bağlamak yeterli kabul edilmez: CSRF, başka kullanıcı process'i, local malware, açık socket ve yetkisiz client riski değerlendirilir. Rastgele session secret, origin kontrolü, process sahipliği, token yaşam döngüsü veya Windows ACL ile gerçek erişim kontrolü kurulur. Named pipe tercih edilirse pipe ACL ve impersonation riskleri test edilir. Model indirme/Agent tool output'u komut olarak değerlendirilmez. Renderer üzerinden keyfi dosya yolu kabul edilmez; canonical trusted root gerekir.

## 14. Agent sınırı: opsiyonel, yetkili, gerçekçi

İlk çalışan hızlı konuşma yolu Agent'a bağlı değildir. Agent yalnız explicit ya da gerçekten güvenilir routing ve kullanıcı izinleriyle açılır; araç yürütme motoru Live'a veya Speech'e kopyalanmaz. Agent çağrısı renderer'dan credential taşıyan serbest HTTP isteği olamaz. Güvenilir Live adapter, policy/onay ve timeout/failure routing uygular. `AGENT_QUERY` gibi gelecekteki özel tokenlar bugünkü modele hazır yetenek sanılmaz.

### 14.1 Metin → ses problemi

Mevcut Kaiwen Speech baseline'ı speech tokenlarıyla çalışır. Agent'ın ürettiği düz metni bu modele verince otomatik doğal konuşma çıkacağına dair public conditioning API'si yoktur. İlk sürümde Agent sonucu ayrı metin panelinde gösterilebilir; seslendirme için ayrıca doğrulanmış TTS bridge veya eğitilmiş Speech text-conditioning gerekir. TTS köprüsü kullanıldıysa “speech-native yanıt” diye gizlenmez; fast path'i gizlice STT→LLM→TTS'e dönüştürmez.

### 14.2 Etkili tool işlemleri

Dosya silme/değiştirme, e-posta, uygulama çalıştırma, ödeme ve veri paylaşma gibi sonuçları olan eylemler doğru bağlamda açık kullanıcı onayı ve Agent policy gerektirir. Düşük güvenli ses tanıma sonucuyla bu araçlar otomatik tetiklenmez. Agent'ın hata vermesi yerel ses oturumunu crash'e götürmez; kullanıcıya metin hata/fallback ve oturuma devam seçeneği sunulur.

## 15. Performans, ölçüm ve gerçek zamanlılık iddiaları

Ölçüm olmadan optimizasyon başarısı ilan edilmez. İlk zorunlu metrik seti:

| Metrik | Sahibi | Yorum |
|---|---|---|
| `first_token_ms` | Speech | Decoder/hoparlör gecikmesi dahil değil |
| `first_pcm_ms` | Speech | İlk decode edilen örnek, henüz duyulmadı |
| `first_pcm_enqueued_ms` | Live | Çalma kuyruğuna kondu; device callback değil |
| `first_audible_audio_ms` | Live | Device output / loopback ölçümüne dayanan tanım |
| `turn_end_to_audio_ms` | Live | Tur bitimi ile ilk duyulabilir output arası |
| `rtf_encode` | Speech | Encode süresi / ilgili ses süresi |
| `rtf_generate` | Speech | Model üretim süresi / üretilen ses süresi |
| `rtf_decode` | Speech | Codec decode süresi / output süresi |
| `peak_device_vram_bytes` | OS/GPU | Runtime, model, codec ve allocator ayrımı |
| `capture_overflow` / `output_underrun` | Live | Her cihazda ölçülen sayı |
| `cancel_ack_ms`, `stale_chunks` | Live | Stop/iptal sonrası gerçek davranış |
| `load_model_cold_ms`, `load_model_warm_ms` | Sidecar | Model indirme süresi hariç ölçüm |

p50/p95/p99 için örnek sayısı, Windows sürümü, power state, CPU/GPU/driver, codec/model release ID, sample rate, buffer boyutu ve warm/cold ayrımı raporda olmalıdır. Speech reposundaki mevcut `scripts/benchmark.py` yalnız tek tam forward latency ölçer; gerçek sesi veya TTFA'yı ölçmüş sayılmaz. Test koşulları eşleşmeyen iki modelin latency grafiği “hızlandı” kanıtı olarak sunulmaz.

### 15.1 Başarı eşikleri ve araştırma sınırı

2 GB VRAM sınıfı cihaz, çok düşük gecikme ve doğal Türkçe ses kalitesi araştırma hedefleridir. Somut p95/RTF eşiği ancak hedef donanımda baseline ölçümü ve kalite tradeoff'u incelenince kabul edilir. “50M parametre model 2 GB'de kesin çalışır” iddiası yasaktır; tam runtime bellek bütçesi gerekir. Batch WAV output küçük parçalara ayrıldı diye modelin TTFA'sı düşmüş sayılmaz.

## 16. Hata sınıfları ve recovery matrisi

Kullanıcıya belirsiz 'Bir şeyler ters gitti' mesajı yerine neden, kapsam ve uygulanabilir geri dönüş sun. Hata kodları protokolde sürümlenir. Hata raporunda gerçek kullanıcı konuşması ve model path'i paylaşılmaz.

| Kategori | Örnek hata kodu — HEDEF | Retry veya güvenli geri dönüş | UI ve sistem davranışı |
|---|---|---|---|
| Mikrofon izni | `MIC_PERMISSION_DENIED` | OS izin değişince yeniden dene | Capture başlamaz, adım açıklanır |
| Giriş aygıtı yok | `AUDIO_INPUT_MISSING` | Başka cihaz seç | Session listening'e girmez |
| Çıkış aygıtı yok | `AUDIO_OUTPUT_MISSING` | Başka cihaz seç | Sahte speaking gösterilmez |
| Device unplug | `AUDIO_DEVICE_LOST` | Yeniden negotiation | Eski queue temizlenir |
| PCM format | `AUDIO_FORMAT_UNSUPPORTED` | Desteklenen örnekleme dön | Sessiz corrupt audio olmaz |
| Sidecar başlatma | `SIDECAR_START_FAILED` | Sınırlı retry / reinstall | UI açık kalır |
| Sidecar zaman aşımı | `SIDECAR_START_TIMEOUT` | Terminate ve bounded retry | Yarım süreç kalmaz |
| Model yok | `MODEL_NOT_INSTALLED` | Kullanıcı onaylı kur | Fake ses otomatik çalmaz |
| Model hash bozuk | `MODEL_INTEGRITY_FAILURE` | Staging sil / önceki sürüm | Dosya aktif edilmez |
| Codec uyuşmazlığı | `CODEC_MODEL_MISMATCH` | Uyumlu paket seç | Inference başlamaz |
| Yetkisiz release | `MODEL_UNTRUSTED_RELEASE` | Güvenilir kaynağa dön | Açık güvenlik açıklaması |
| GPU bellek | `MODEL_OOM` | Destekli hafif model/CPU | Sonsuz retry yok |
| IPC transport | `TRANSPORT_DISCONNECTED` | Yeni epoch, yeniden bağlan | Stale chunk atılır |
| Queue overflow | `AUDIO_QUEUE_OVERFLOW` | Defined drop/fail | Sayaç/log ve kullanıcı bildirimi |
| Generation timeout | `GENERATION_TIMEOUT` | Cancel ve gerektiğinde retry | Sonsuz spinner yok |
| Boş output | `MODEL_EMPTY_OUTPUT` | Kullanıcıya anlamlı hata | Ses çıkmış gibi başarı yazılmaz |
| Protokol majör | `PROTOCOL_UNSUPPORTED` | Uyumlu sidecar/app | Handshake reddi |
| Agent yok | `AGENT_UNAVAILABLE` | Ses yolu devam veya text fallback | Mikrofon kapanmaz |

Sistem `failed` durumuna girdiğinde hangi kaynakların açık kaldığı test edilir: mic, speaker, model, pipe, temp WAV ve child PID. Retriable hata sonrası yeni generation/epoch yapılmadan eski output dinletilmez. HTTP 200 veya başarılı RPC ACK'i, codec output'unun geçerli olduğunu tek başına kanıtlamaz. Hatalar kod ile kullanıcı mesajı arasında type-safe eşleme üzerinden aktarılır.

### 16.1 Kullanıcıya görünür hata eylemleri

`MIC_PERMISSION_DENIED`: “Mikrofon izni kapalı. Windows Ayarları'ndan izin verip yeniden dene.” `CODEC_MODEL_MISMATCH`: “Seçili ses modeli bu codec ile uyumlu değil; desteklenen model paketini seç.” `SIDECAR_START_FAILED`: “Yerel ses motoru başlatılamadı. Tekrar dene veya tanı raporunu aç.” `MODEL_OOM`: “Bu cihazda model için yeterli GPU belleği yok; daha hafif bir model seç.” Bu mesajlar açıklayıcıdır; çalışmayan bir düğme, sahte kurulum sihirbazı veya belirsiz “Başardı!” animasyonu üretme.

## 17. Windows paketleme, dağıtım ve güncelleme

Windows pilot için Electron app, Python sidecar, ses cihazı bileşenleri, gerekiyorsa FFmpeg/runtime **temiz cihazda** çalışmalıdır. Geliştiricinin PATH'inde Python olduğu için açılan uygulama paketleme kanıtı değildir. Exe/dll mimarisi, native Node ABI, ASAR/unpacked konumları, spawned process cwd, path quoting ve antivirus davranışı test edilir.

1. App sürümü, sidecar protokol aralığı ve desteklediği Speech release sürümü belgelenir.
2. Sidecar exe konumu sabit/verified packaged resource dizininden çözülür; renderer arbitrary executable seçemez.
3. Kullanıcı verileri kurulum dizinine değil OS user-data dizinine gider; upgrade/uninstall saklama politikası açıktır.
4. Updater eklendiğinde imza, release hash ve rollback olmadan silent auto-install açılmaz.
5. Release asset SHA-256, imza/trust kökü, Git tag ve package version tutarlılığı doğrulanır.
6. Test raporunda Windows versiyonu, CPU/GPU/driver, mic yokluğu ve ilk açılış ayrı kaydedilir.
7. Installer model ağırlıklarını varsayılan olarak gizlice bundle veya indir etmez; kullanıcı onaylı model kurulumuna geçilir.
8. Rollback uygulama + sidecar + model manifest uyumluluğunu birlikte ele alır; önceki exe yeni release'i okuyamayabilir.
9. Update sırasında konuşma aktifse oturum güvenle kapatılmadan sidecar silinmez.
10. Native ses DLL'i değiştiğinde cihaz kullanımda ve uygulama kapalı koşulları ayrı test edilir.

Kaynak kodu değiştirmek ile GitHub release yayınlamak farklı yetkilerdir. Ajan açık kullanıcı isteği olmadan tag, public GitHub release veya kullanıcı makinesine dağıtım yapmaz. Yerel installer build edilebilir ancak gerçek test sonuçları ve paketleme uyarıları açık raporlanır.

## 18. CI/CD ve kalite kapıları

Mevcut `kaiwen-live` repo'sunda CI ve paket altyapısı henüz bulunmuyor olabilir. Aşağıdaki komutlar **HEDEF** olup gerekli `package.json`, Python project ve gerçek scriptler oluşturulduktan sonra çalıştırılır. npm/pnpm/uv tercihi repo genelinde tutarlı olmalı; iki lockfile aynı proje için rakip kaynak olmamalıdır.

```bash
# HEDEF / NOT IMPLEMENTED — package.json scriptleri kurulunca geçerli:
npm ci
npm run lint
npm run typecheck
npm run test
npm run build

# HEDEF / NOT IMPLEMENTED — Python sidecar projesi kurulunca geçerli:
python -m pip install -e 'apps/sidecar[dev]'
python -m pytest apps/sidecar/tests -q
python -m ruff check apps/sidecar
```

GitHub Actions temiz checkout üzerinde TS strict typecheck, lint, renderer unit, protocol schema fixture, Python lint/test ve Electron packaging smoke testlerini çalıştırmalıdır. Windows audio API veya native modül varsa Windows runner derlemesi zorunludur. Bulut CI fiziksel mikrofon ve gerçek GPU sunmayabilir; `hardware tests not run` ayrı durumdur. Sahte fixture ile geçen testleri gerçek donanım testi diye bildirme.

### 18.1 PR kalite kontrolü

Public event/IPC contract değişiminde schema, producer ve consumer fixture beraber güncellenir. Dependency değişirse lockfile yenilenir ve lisans/CVE/SBOM etkisi incelenir. Açıklamada performans, gizlilik, ses cihazı davranışı, geriye uyumluluk ve rollback yer alır. Görsel değişiklikte dark/light ekran görüntüsü, keyboard tab order, reduced motion ve focus test edilir. `README.md` implementation status tablosu gerçek kanıt olmadan üst seviyeye çıkarılmaz.

## 19. Negatif test matrisi ve test kimlikleri

Testler tekrarlanabilir ve belli device/protocol koşullarına sahip olmalıdır. Aşağıdaki isimler hedef test senaryolarıdır; repoda bugün test dosyası bulunduğu anlamına gelmez.

| ID | Girdi/hata | Beklenen sonuç |
|---|---|---|
| `LIVE-U01` | IPC bilinmeyen action | Güvenli schema reject |
| `LIVE-U02` | Limitten büyük PCM chunk | Bellek şişmeden red |
| `LIVE-U03` | Negatif `sample_index` | Validation error |
| `LIVE-U04` | Duplicate sequence | Ses iki defa çalmaz |
| `LIVE-U05` | Out-of-order sequence | Gap/order politikası çalışır |
| `LIVE-U06` | Eski session epoch | PCM discard |
| `LIVE-U07` | Yanlış generation ID | Başka yanıt dinletilmez |
| `LIVE-U08` | Playback iki kere stop | Idempotent; crash yok |
| `LIVE-U09` | Generation iki kere cancel | Idempotent; leak yok |
| `LIVE-U10` | Kapalı session'a audio | Kontrollü red |
| `LIVE-U11` | `end_turn` iki kere | Tek generation başlar |
| `LIVE-U12` | Kapanış/generation yarışı | Kaynaklar serbest |
| `LIVE-U13` | Model ready değil | Inference başlamaz |
| `LIVE-U14` | Desteklenmeyen protokol major | Handshake fail closed |
| `LIVE-U15` | Yanlış codec vocab/kimliği | Release reddi |
| `LIVE-U16` | SHA-256 bozulmuş model | Aktivasyon yok |
| `LIVE-U17` | Archive path traversal | Güvenli dizin dışına yazmaz |
| `LIVE-U18` | Mic izni reddi | Capturing olmaz, UX uyarır |
| `LIVE-U19` | Input cihazı çıkarılır | Recovery, deadlock yok |
| `LIVE-U20` | Output cihazı çıkarılır | Playback durur, kaynak bırakır |
| `LIVE-U21` | Queue kapasitesi dolar | Bounded backpressure |
| `LIVE-U22` | Sidecar GPU OOM | Güvenli fail, sınırlı retry |
| `LIVE-U23` | Sidecar aniden kapanır | UI açık, cihaz temiz |
| `LIVE-U24` | Exe yok veya AV blok | Eylemli hata, sahte ready yok |
| `LIVE-U25` | Close sırasında generation | Mic/speaker/PID cleanup |
| `LIVE-U26` | Windows sleep/resume | Device renegotiate |
| `LIVE-U27` | Ağ yok, model zaten yüklü | Temel yerel görüşme sürer |
| `LIVE-U28` | PCM JSON yerine binary beklentisi | Payload tipi doğrulanır |
| `LIVE-U29` | Boş output/EOS | Sahte sesi başarı saymaz |
| `LIVE-U30` | Agent servisi kapalı | Ana konuşma devam eder |
| `LIVE-U31` | Tool yetkisi yok | Yan etki olmaz, red döner |
| `LIVE-U32` | Ses/transkript log'a yazılır | Privacy test ihlali yakalar |
| `LIVE-U33` | Aktif oturumda model hot-swap | Eski session korunur veya durur |
| `LIVE-U34` | Çift UI event subscribe | Listener leak oluşmaz |
| `LIVE-U35` | Çok uzun turn | Limit, açık kullanıcı mesajı |
| `LIVE-U36` | Native streaming parity | Batch/incremental tolerans kontrolü |
| `LIVE-U37` | Cancellation ACK geç kalır | UI race ve stale output yok |
| `LIVE-U38` | Audio callback stall | Underrun sayacı, loop bloklanmaz |
| `LIVE-U39` | Güvensiz release imzası/issuer | Trust policy uygular |
| `LIVE-U40` | Temiz Windows kurulum | Paketli app ve sidecar smoke |

Bunların hepsi ilk PR'da yazılmaz; LIVE0–LIVE12 teslimlerine dağıtılır. `LIVE-U36`, Speech native streaming API üretildiğinde uygulanabilir, aksi halde `NOT_IMPLEMENTED` kalmalıdır. Test kırmızıysa testi silerek yeşile dönüştürmek yasaktır. Donanım yoksa mock ile pass gösterip kanıt türünü değiştirme. Sürüm fixture'ı değişirken eski sürümün geri dönüş testi de tutulmalıdır.

### 19.1 Test veri kalitesi

Kısa izinli Türkçe konuşma, sessizlik, clipping, aşırı düşük ses, arka plan gürültüsü, uzun tek tur, yanlış sample rate, kesik PCM, bozuk WAV header, iki cihaz, headset ve hoparlör echo örnekleri sağlanmalıdır. Ses fixture'larının kaynak/izin/süre/sample rate/hash metadata'sı yazılır. Test deterministik olabilir fakat gerçek kullanımın kapsamını temsil edip etmediği ayrıca belirtilir. Konuşmacı kimliğinin doğrulanmadığı sesleri çoklu konuşmacı testinin ground truth'u gibi gösterme.

## 20. Gerçek Windows pilot cihaz protokolü

En az bir Windows cihaz profili için aşağıdaki adımlar uygulanır:

1. Windows sürümü, CPU, GPU, driver, RAM, mikrofon, çıkış aygıtı ve sample-rate modu kaydedilir.
2. Temiz paket kurulumu yapılır, ilk açılışta model yok durumunun UI'ı doğrulanır.
3. Kullanıcı açıkça mikrofon izni verir; OS mic handle açılması gözlemlenir.
4. Gerçek konuşma 10 saniye kaydedilir; gerçek PCM sample sayısı ve capture timestamp'i kaydedilir.
5. Loopback'te hoparlörden ses duyulduğu doğrulanır; yankı/feedback not edilir.
6. Güvenilir Speech checkpoint varsa codec'le gerçek audio→audio turu tamamlanır.
7. Stop, cancel ve yeniden konuşma testi yapılır; eski sesin geri dönmediği doğrulanır.
8. Input/output cihazı değişir, unplug/replug ve default seçim test edilir.
9. Sidecar kasıtlı sonlandırılır; UI ve restart davranışı incelenir.
10. Windows sleep/resume sonrasında ses yolu doğru recovery yapar veya güvenli hata gösterir.
11. Uzun oturumda memory, child process, listener, queue ve handle birikimi ölçülür.
12. Uygulama kapanınca açık capture/sidecar PID kalmadığı OS araçlarıyla kontrol edilir.

Gerçek donanım testleri çalıştırılmadıysa “Windows uyumlu sesli asistan” gibi genel iddia yazılmaz. Kulaklık ve açık hoparlör otomatik barge-in kalitesi açısından ayrı test profilleridir.

### 20.1 Test raporu şema örneği — HEDEF

```json
{
  "test_id": "LIVE-HW-BATCH-001",
  "status": "NOT_RUN",
  "run_mode": "batch_real",
  "platform": "windows",
  "device_profile_id": "to_be_recorded",
  "speech_release_id": null,
  "codec_id": null,
  "sample_rate_hz": 24000,
  "captured_frames": null,
  "first_audible_audio_ms": null,
  "peak_device_vram_bytes": null,
  "audio_output_verified_by_user": false,
  "reason": "Örnek şema; test henüz çalıştırılmadı"
}
```

`NOT_RUN`, `FAIL` ve `SKIP` ayrı anlamlar taşır. Ölçülmemiş metrik alanı keyfi `0` yapılmaz. Test sessizlik yerine gerçekten konuşmayı aldı mı, bunun için sesin kişisel kayıt olarak repo'ya koyulması gerekmez; izinli analiz istatistikleri ve kontrollü lokal dinleme yeterlidir.

## 21. UX, erişilebilirlik ve gerçek durum göstergeleri

İlk UI tek bir ana konuşma ekranı, seçili model, input/output cihazı seçimi, mikrofon aç/kapat, stop/cancel ve basit ayarlar içerir. Kullanıcı `listening`, `processing`, `speaking` ve `failed` durumunu açık Türkçe metinle görebilir. `listening`, gerçek OS capture sinyalinden; `speaking`, device playback sinyalinden türetilmelidir. Audio waveform'un hareketi tek başına bu durumların kanıtı değildir.

- Mikrofon kapalıyken “dinleniyor” denmez; OS privacy indicator ile UI farklıysa hata raporlanır.
- Model yoksa kontrolsüz yükleme animasyonu devam etmez; kullanıcıya kurulum ve geri dönme seçenekleri sunulur.
- Gerçek model ses üretmediğinde hayali transkript, fake konuşma balonu veya sahte “Cevap hazır” yazılmaz.
- Ana kontroller klavyeyle erişilebilir; focus ring, screen reader label, contrast ve reduced motion test edilir.
- UI yalnız renkle durum anlatmaz; readable text ve ARIA live status kullanır.
- Ses animasyonu GPU/CPU iş yüküyle audio callback'i etkileyemez; yoğun ekran çizimi sırasında underrun ölçülür.
- Stop kontrolü inference sırasında bile klavye ile ulaşılabilir kalır; modals veya loader input'u bloklamaz.
- Otomatik VAD güvenilir değilse kullanıcıya manuel “Konuşmayı bitir” kontrolü verilir.
- Speech'in ürettiği sesin transkripti model tarafından sağlanmıyorsa, UI bunun otomatik transkript olduğunu varsaymaz.
- Uygulama offline ise Agent veya model indirme durumları açıkça ayrılır; asıl yerel konuşma açıkça kullanılabilir kalır.

### 21.1 Design paketini kullanma kuralı

Komponent ihtiyacı doğarsa `kaiwen-design` paketinin mevcut exports, responsive davranışı ve theme token'ları önce incelenir. Eksik bir ortak bileşen Design'da geliştirilebiliyorsa ayrı repo PR'ı önerilir; Live'ın içindeki uygulama özel bileşenler burada tutulur. Tasarım sistemi import adı, npm sürümü, bağımlılık çözümü ve Storybook/Docs bağlantısı doğrulanmadan hayali kurulum komutu verilmez. Dark/light state tek kaynaktan yönetilir, CSS override'lar ortak bileşeni kalıcı olarak bozmaz.

## 22. Konfigürasyon, ayarlar ve migration

Config tek merkezden tipli ve runtime doğrulanan şemayla okunur. Dosya versiyonu, varsayılanlar ve kullanıcı kontrollü ayarlar ayrı tutulur. Aşağıdaki örnek **henüz uygulama şeması değil**, tasarım fikstürüdür:

```yaml
# HEDEF / NOT IMPLEMENTED
schema_version: 1
app:
  locale: tr-TR
  telemetry_opt_in: false
  auto_start_microphone: false
speech:
  runtime_mode: batch_real
  model_release_id: null
  max_sessions: 1
  inference_timeout_sec: 120
  auto_download: false
audio:
  input_device_id: default
  output_device_id: default
  sample_rate_hz: 24000
  capture_chunk_ms: 20
  playback_buffer_ms: 80
  enable_auto_barge_in: false
security:
  local_only: true
  auto_install_updates: false
```

Burada `model_release_id: null` iken `batch_real` seçili olsa bile gerçek runtime `MODEL_NOT_INSTALLED` döner; sahte audio ile devam etmez. 20 ms capture ve 80 ms playback tamponu **ölçülmemiş öneri başlangıç değeridir**, tüm cihazlarda uygun olduğu iddia edilmez. Timeout GPU/CPU ve gerçek model profiline göre gerekçelendirilir. Auto-download yalnız açık kullanıcı onayıyla yapılır.

### 22.1 Migration güvenliği

Ayar şeması yükseltildiğinde eski uygulamanın kayıtları izinsiz silinmez. `schema_version=0`, `=1`, bozuk JSON/YAML, bilinmeyen enum, eski model ID, eksik device ID ve uygulama güncellemesi sırasında yarım yazılmış config test edilir. Yazma işlemi geçici dosya + atomik replace ile yapılır; bir önceki sağlam config korunabilir. “Güvenli varsayılan” mikrofonun otomatik açık olmasına döndürülmez. Silme/reset işlemi yalnız ilgili alanı etkiler; `userData` dizininin tamamına kör temizleme yapılmaz.

## 23. Ajanın aşamalı uygulama planı: LIVE0–LIVE12

| Aşama | Minimum teslim | Kabul kanıtı |
|---|---|---|
| **LIVE0 — Repository Foundation** | TS/Python iskeleti, lockfile, lint/typecheck/test/CI | Temiz checkout'ta gerçek komutlar |
| **LIVE1 — Electron Shell** | Main/preload/renderer, dar IPC, Design | Pencere aç/kapa, IPC allowlist testleri |
| **LIVE2 — Audio Loopback** | Gerçek mic, speaker, permission, cihaz seçimi | OS cihazından alınıp duyulan ses |
| **LIVE3 — Fake Sidecar** | Process supervisor, handshake, state machine | Deterministik fake, crash, cancel testleri |
| **LIVE4 — Batch Real Speech** | Güvenilir checkpoint ile `kaiwen_voice` adapter | Türkçe gerçek audio→audio tek tur |
| **LIVE5 — PCM Transport** | Binary PCM, bounded buffer, sequence/epoch | Overflow ve stale chunk testleri |
| **LIVE6 — Model Library** | Forge release manifest, hash, activation/rollback | Bozuk model reddi, güvenli geçiş |
| **LIVE7 — Observability** | TTFA, RTF, device VRAM, redacted logs | Cihaz/fixture bazlı pilot benchmark |
| **LIVE8 — Chunked Output** | Parçalı gerçek PCM ve stop playback | Sıra, underrun ve stale output testleri |
| **LIVE9 — Native Streaming** | Speech SDK hazırsa incremental adapter | KV/codec parity ve ses cihazı ölçümü |
| **LIVE10 — Barge-in** | Güvenli manuel kesme, sonra AEC/VAD otomasyon | Echo ve yanlış kesme testleri |
| **LIVE11 — Windows Release** | Packaged sidecar, installer, update/rollback | Temiz makine smoke + imza politikası |
| **LIVE12 — Optional Agent** | İzinli tool routing ve text/audio köprüsü | Approval ve no-agent fallback testleri |

Bu tablo “tek PR'da hepsini oluştur” talimatı değildir. Milestone sınırı, gözlenebilir davranış ve test sayısı ile tanımlanır. **İlk büyük sonuç LIVE4: gerçek kullanıcı sesi gerçek yerel modelden gerçek konuşma sesi üretir.** LIVE9 Speech native runtime implementasyonuna bağımlıdır. LIVE12 ilk demo için blocker değildir. Uygulama akışı yalnız gereği varsa yeniden sıralanabilir; gerekçe ve bozulan test raporu tutulur.

### 23.1 DoR, DoD ve Release Gate

**Definition of Ready:** Girdi/çıktı açık, beklenen davranış yazılı, donanım ve veri izinleri biliniyor, producer contract durumu doğrulandı, rollback ve en az bir negatif test tanımlandı. **Definition of Done:** Kod çalışıyor; etkilenen şema fixture'ları, typechecks, unit ve integration testleri geçti; gizlilik ve kaynak yaşam döngüsü incelendi; kullanıcı durumu doğru; kanıt ve dokümantasyon güncel. **Release Gate:** Paketlenmiş Windows sürümü ve gerçek ses cihazı testleri ayrıca tamamlandı; bir PR'ın yeşil olması release izni değildir.

## 24. Her değişiklikte çalıştırılması gereken doğrulamalar

Her görev kendine uygun en küçük ama eksiksiz kontrol setini gerektirir. Asgari standart sırası şöyledir:

1. Değişen fonksiyon/event için unit ve runtime schema testleri.
2. TypeScript strict typecheck, Python statik kontrol ve lint.
3. Fake sidecar'da session, cancellation, duplicate/stale message testleri.
4. Değişen cross-repo sınır için üretici–tüketici contract fixture testleri.
5. Gerçek Speech entegrasyonu değiştiyse güvenilir checkpoint ve codec load/response smoke.
6. Electron main/preload veya security değiştiyse packaged build ve IPC permission testleri.
7. Audio callback/driver değiştiyse gerçek Windows cihaz pilotu veya açık `NOT_RUN` bildirimi.
8. Model release/installer değiştiyse hash, trust, activation, rollback ve upgrade testleri.
9. Performans değiştiyse aynı fixture ve cihaz profilinde before/after benchmark.
10. UI değiştiyse keyboard, erişilebilir metin, reduced motion ve tema kontrolü.

Ajan test komutunu çalıştırmadan `PASS` yazamaz. Ortamda gerekli GPU/mic yoksa `NOT_RUN`, nedeni, riski ve testin nasıl çalıştırılacağı yazılır. CI başarısızken iş “tamamlandı” denmez. Test kodunu gevşetmek yalnız önceki beklentinin hatalı olduğu kanıtlandığında ve yeniden tanımlandığında kabul edilir. “Kod derlendi” tek başına kullanıcıya ses ulaştığının kanıtı değildir.

## 25. Güvenlik ve kullanıcı verisi için kırmızı çizgiler

Aşağıdakiler kullanıcının açık izni ve güvenlik incelemesi olmadan yapılmaz:

- Mikrofonu başlangıçta gizlice açmak, background voice kaydı almak veya kişisel sesi sürekli dinlemek.
- PCM/transkript/Agent yanıtını analytics servisine, dış sunucuya veya üçüncü taraf API'ye varsayılan göndermek.
- Doğrulanmamış binary, model ağırlığı, pickle, `.pt` veya zip'i rastgele kaynaktan açmak/çalıştırmak.
- Renderer'a keyfi shell, Node, filesystem, network veya kimlik bilgisi erişimi vermek.
- Model artifact'ini izinsiz/uyumsuz lisansla yeniden dağıtmak veya gizlice büyük dosya indirmek.
- Düşük güvenli speech token yorumundan etkili Agent aracı çalıştırmak.
- Agent output veya indirilen metadata'yı sistem komutu veya üst seviye talimat olarak uygulamak.
- Gerçek görüşme kaydını PR, issue, CI artifact veya GitHub release'e koymak.
- Model yüklenemezken fake ses çalarak “Başarılı konuşma” göstermek.
- Kullanıcı veri dizinini, model kütüphanesini veya config'i izinsiz toplu sıfırlamak.
- Public TCP servis veya yanlış ACL'li named pipe'ı sessizce etkinleştirmek.
- İlgili release testleri olmadan otomatik background update ile aktif ses oturumunu değiştirmek.

Güvenlik uyumsuzluğunda güvenli fonksiyon kaybı tercih edilir: `unsupported`, `permission_required` veya `not_ready` gösterilir; gizli workaround kurulmaz. Güvenlik kontrolünü kapatan PR'lar açık ADR ve uzman gözden geçirmesi gerektirir.

## 26. Her görev sonunda zorunlu Codex raporu

Ajan tamamladığı görevi aşağıdaki kanıt formatıyla raporlar. Bu şablon raporun kendisidir; otomatik artifact üretildiği iddia edilmez.

```markdown
## Değişiklik özeti
- Hedef: LIVE? / tek ölçülebilir kabul kriteri
- Gerçeklenen: ...
- Kapsam dışı: ...

## Kanıt
- Repo/branch/commit: ...
- Değişen dosyalar: ...
- Gerçek çalıştırılan komutlar: ...
- Sonuç: PASS / FAIL / NOT_RUN, exit code ve test sayısı
- Gerçek audio testi: cihaz/fixture/sonuç veya NOT_RUN
- Model ve codec release: hash/ID veya NOT_APPLICABLE
- Performans: örnek sayısı, p50/p95, VRAM veya NOT_MEASURED

## Güvenlik ve uyumluluk
- IPC/session contract etkisi: ...
- Secrets/audio/data retention etkisi: ...
- Geriye uyumluluk ve rollback: ...

## Açık kalanlar
- Riskler, sınırlamalar ve sonraki küçük görev: ...
```

“CI başarılı” için gerçek run ID/çıktısı, “WAV hoparlörden çalındı” için cihaz kanıtı, “2 GB sınıfı uyumlu” için bütün cihaz belleği ölçümü, “native streaming” için artımlı model/codec deney raporu gerekir. Çok sayıda screenshot bu sonuçları ikame etmez. Kullanıcıya gerçek ses kaydını göndermeden önce mahremiyet ve izin politikası uygulanır.

### 26.1 Definition of Done — tek Live görevi

İstenen davranış gerçekten çalışıyor mu? Mevcut kullanıcı verisi korunuyor mu? Public API/IPC etki analizi tamam mı? Hem olumlu hem olumsuz yol test edildi mi? UI gerçek state'i mi gösteriyor? Güvenlik ve mahremiyet etkisi incelendi mi? Regression testleri geçti mi? Fiziksel cihaz gerekiyorsa test edildi mi veya kısıt açık raporlandı mı? Dokümantasyon kodla uyumlu mu? Rollback yolu var mı? Zorunlu bir cevap “hayır” ise görev `PARTIAL`/`BLOCKED` olarak raporlanır; kodun yazılmış olmasıyla tamamlanmış sayılmaz.

## 27. Yasak anti-pattern'ler

| Yanlış yaklaşım | Neden yanlış? | Doğru yöntem |
|---|---|---|
| UI'ı tek `App.tsx` içinde büyütmek | Race ve state sahipliği kaybolur | Feature/session ayrımı |
| Tüm kodu dev bir `main.ts` içine koymak | Process/audio/test riskleri artar | Main controller, audio ve adapter |
| Fake PCM'i gerçek AI sesi sunmak | Kullanıcıyı yanıltır | Fake etiketi, ayrı fixture |
| Batch WAV'i parçalamayı native streaming saymak | Gerçek model performansı ölçülmez | Dört runtime modunu ayır |
| Playback stop'u generation cancel sanmak | GPU işi ve eski ses sürebilir | Ayrı stop/cancel/epoch |
| Audio callback'te inference | Drop ve deadlock | Bounded queue + worker |
| Sınırsız PCM queue | Bellek ve gecikme artar | Backpressure limitleri |
| Eski epoch'ları kabul etmek | İptal sonrası eski ses döner | Epoch/generation filtreleme |
| Bilinmeyen codec release yüklemek | Ses bozulur, güven sorunu | Metadata/hash/trust |
| Renderer'a geniş Node yetkisi vermek | Komut/dosya saldırısı | Dar preload bridge |
| Transcript'ten konuşma kalitesi varsaymak | Speech-native kalite kanıtı değildir | Gerçek dinleme ve senaryo testleri |
| Tool metnini otomatik konuşturmak | Text→speech yeteneği yok olabilir | Testli bridge veya text panel |
| Agent'i her tur için şart koşmak | Local-first ve hız bozulur | Opsiyonel Fast Path dışı Agent |
| Güncelleme sırasında otomatik hot swap | Aktif ses ve uyumluluk bozulabilir | Sürüm pin ve rollback |
| “Sıfır gecikme/2 GB” garantisi | Kanıtsız | Cihaz ve fixture ölçümü |
| PCM/transkript'i loglamak | Veri gizliliği | Redacted telemetry |
| Linux CI'ı Windows ses testi saymak | Sürücü hataları gizlenir | Gerçek Windows pilot |
| İlk PR'da 13 milestone'u birden yapmak | Test ve bakım zorlaşır | Küçük, doğrulanabilir PR |

Yeni bir teknolojinin varlığı onu ilk sürüme ekleme gerekçesi değildir. Kullanıcı tek dosya veya tek geliştirme görevi istediyse yalnız o kapsamda değişiklik yapılır.

## 28. Son kontrol listesi — Live V1 kabulü

- [ ] Electron shell, güvenli preload ve React UI gerçekten build ediliyor.
- [ ] Windows mikrofon/hoparlör ile gerçek loopback test edildi.
- [ ] Sidecar child-process lifecycle, health, crash ve cleanup testleri geçti.
- [ ] Fake/batch/chunked/native modların etiketleri doğru ve kanıta bağlı.
- [ ] Uyumlu gerçek Speech checkpoint/codec ile Türkçe audio→audio yanıt üretildi.
- [ ] Stop playback, cancel generation, stop mic, close session ayrı test edildi.
- [ ] `session_epoch`, sequence ve generation bazlı stale output reddi çalışıyor.
- [ ] PCM format, channel, byte count ve buffer limitleri tanımlı ve testli.
- [ ] Kurulan model manifest, hash, trust ve codec kimliğiyle doğrulanıyor.
- [ ] Yanlış sürüm/bozuk dosya/yanlış codec güvenli biçimde reddediliyor.
- [ ] Agent yokken yerel konuşma deneyimi çalışıyor.
- [ ] Kullanıcı sesi varsayılan kalıcı saklanmıyor veya ağa gönderilmiyor.
- [ ] Donanım/OS/model kimlikli TTFA, RTF, VRAM ve underrun raporu var.
- [ ] Erişilebilir stop, hata, izin ve cihaz seçimi ekranları test edildi.
- [ ] Temiz Windows kurulumunda sidecar/installer smoke kanıtı var.
- [ ] Gerçek çalıştırılan test komutları ve CI sonuçları raporlandı.
- [ ] README, API sözleşmesi, ADR ve statü tablosu gerçek sonucu anlatıyor.

Bu liste **gelecekteki ürün kabul koşullarıdır**; bugünkü tamamlanmış işlerin listesi değildir. Yeni belge dosyası tek başına Live V1 hazır anlamına gelmez. Sıradaki dosya `docs/ARCHITECTURE.md` olacaktır; AGENTS ajan davranışlarını ve kalite sınırlarını, ARCHITECTURE bileşenlerin teknik kontratlarını tanımlar.

---

## Ek A — Terimler

| Terim | Anlam |
|---|---|
| `audio callback` | OS ses sürücüsünün kısa zaman penceresinde çağırdığı kod; model işi yok |
| `barge-in` | Kullanıcının asistan konuşurken sesli/manuel kesmesi |
| `batch inference` | Turn bittikten sonra bütün output'u üretme |
| `chunked playback` | Hazır PCM'yi taşıma parçasına bölme; native model streaming değildir |
| `native streaming` | Codec/Transformer artımlı üretim ve decoder state |
| `session_epoch` | Eski generation olaylarını yeni konuşmadan dışlama sayacı |
| `sequence` | Stream içindeki sıralama ve tekrar denetimi |
| `RTF` | İşleme süresinin üretilen/işlenen ses süresine oranı |
| `TTFA` | İlk ses gecikmesi; generated/queued/audible ayrımı vardır |
| `release manifest` | Model/codec artifact ve uyumluluk sözleşmesi |
| `trust root` | Artifact veya imza doğrulamasında güvenilen kimlik/kaynak |
| `feature negotiation` | Client ve sidecar'ın ortak destekledikleri fonksiyonlarda anlaşması |
| `DoR` / `DoD` | İşe başlamadan hazır olma / işi tamamlanmış kabul etme kriterleri |

## Ek B — İlgili belge ve sözleşmeler

- [Live README](README.md): ürün vaadi, mevcut durum ve LIVE0–LIVE12 sırası.
- `docs/ARCHITECTURE.md`: sıradaki dosya; sidecar, OS ses sürücüsü, transport, session ve lifecycle mimarisi.
- `docs/DESIGN_AND_UX.md`: sonraki dosya; görsel akış, erişilebilirlik, tema ve ekranlar.
- `docs/AGENT_INTEGRATION.md`: sonraki dosya; araç yönlendirme, izin, Agent görevleri ve sesli yanıt problemi.
- [Workspace Integration](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/INTEGRATION.md): cross-repo wire protocol ve sorumluluk sınırları.
- [Speech API](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/API.md): mevcut Python API ve hedef session SDK.
- [Speech Streaming](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/STREAMING.md): KV cache, codec state ve streaming parity.
- [Speech Performance](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/PERFORMANCE.md): cihaz, gecikme ve VRAM doğrulama metodu.
- [Forge Registry](https://github.com/ImtheKaiwen/kaiwen-forge/blob/8bf2af3b925bc1478328b4a26fcba36af74480fb/docs/MODEL_REGISTRY.md): release manifest, trust ve rollback.
- [Engineering Standards](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/ENGINEERING_STANDARDS.md): çapraz proje güvenlik/kalite kuralları.
- [Workspace Roadmap](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/ROADMAP.md): milestone koordinasyonu ve öncelik.

Üretici–tüketici sözleşmeleri çelişirse hangi tarafta gerçek kaynak kodu ve sürümlü şema bulunduğunu bul; yeni belgeyi tek taraflı protocol source of truth ilan etme. **Önce çalışan ses hattını kanıtla; sonra streaming, kalite ve ürün ölçeğini artır.**
