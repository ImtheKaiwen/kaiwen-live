# Kaiwen Live — Agent Entegrasyonu: Niyet, Yetki, Asenkron Görev ve Sesli Yanıt Sözleşmesi

> **Belge:** `kaiwen-ai/kaiwen-live/docs/AGENT_INTEGRATION.md`  
> **Durum:** **HEDEF MİMARİ / GELİŞTİRME ŞARTNAMESİ.** Buradaki Live adapter, IPC komutları, intent router ve sesli Agent sonucu henüz uygulanmış değildir.  
> **Sahip:** Kaiwen Live (ürün entegrasyonu); Kaiwen Agent (model/araç/policy/approval runtime); Kaiwen Speech (speech-native model ve codec).  
> **İlk teslim:** Türkçe konuşma ana yolunu bozmadan, kullanıcı tarafından açıkça talep edilen **tek güvenli Agent metin isteğinin** yerel Python bridge üzerinden çalıştırılması ve sonucunun Live içinde gösterilmesi.  
> **Gelişim sırası:** Agent kapalı → test/fake bridge → gerçek text-only chat → izinli read-only action → gerçek approval → job/cancellation → açık TTS/koşullandırma → araştırma niteliğinde öğrenilmiş audio-control token.  
> **Doğrulanan kaynaklar:** [Live README](../README.md), [Live AGENTS](../AGENTS.md), [Live Architecture](ARCHITECTURE.md), [Live Design & UX](DESIGN_AND_UX.md), [Workspace Integration](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/INTEGRATION.md), [Speech API](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/API.md), [Speech Streaming](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/STREAMING.md), [Forge Model Registry](https://github.com/ImtheKaiwen/kaiwen-forge/blob/8bf2af3b925bc1478328b4a26fcba36af74480fb/docs/MODEL_REGISTRY.md), [Kaiwen Agent GitHub](https://github.com/ImtheKaiwen/kaiwen-agent).

---

## 1. Amaç, kapsam ve teknik dürüstlük

Kaiwen Live'ın ana değeri **yerel, Türkçe, speech-native konuşma**dır. Kaiwen Agent ise bilgi erişimi, karmaşık akıl yürütme, araç kullanımı, doğrulanabilir görev yürütme, izinler ve dış sistemlere yapılan işlemlerden sorumlu ayrı kütüphanedir. Bu iki yeteneğin bir üründe bulunması, konuşma modelinin kendisini bir LLM veya tool-calling modeli yapmaz. Normal sesli konuşma ile Agent görevleri farklı gecikme, maliyet, güvenlik ve durum yönetimi sınırlarına sahiptir.

Bu belge şu sorulara yanıt verir: Hangi istekte Agent devreye girecek? Sesten veya UI'dan gelen bir istek nasıl doğrulanacak? Agent'a hangi bilgi aktarılacak? Hangi araçlar onay gerektirecek? Agent çalışırken konuşma nasıl devam edecek? Kullanıcı konuşmayı kestiğinde dış dünyadaki işlem neden otomatik geri alınmış sayılmayacak? Metinsel Agent sonucu, mevcut Speech modeli text-to-speech desteklemiyorken nasıl doğru sunulacak? Dış sistem başarısız olursa Live nasıl güvenilir geri bildirim verecek?

### 1.1 Durum etiketleri

| Etiket | Anlamı | Kanıt gereği |
|---|---|---|
| **MEVCUT — Agent** | `kaiwen-agent` içinde gerçekten bulunan sınıf/fonksiyon | Kaynak API ve paket sürümü |
| **MEVCUT — Speech** | `kaiwen_voice` içindeki mevcut inference/codec API | Kaynak kod, örnek CLI |
| **HEDEF — Live** | Gelecekte yazılacak bridge, ekran, IPC, session adapter | Kod, sözleşme ve test henüz gerekli |
| **DENEYSEL** | Speech control token, text conditioning, otomatik intent veya native tool-voice | Araştırma deneyleri ve ölçüm |
| **TEST FAKE** | Mock provider, sabit transcript veya sentetik PCM | Sadece sözleşme ve UI testi |

30 Ekim 2026'da `kaiwen-live` GitHub reposu yalnız kısa başlangıç README'sini içeriyordu. Bu klasöre hazırlanan ayrıntılı Markdown belgeleri **çalışan Electron uygulaması değildir**. Kaiwen Agent Python paketi `kaiwen-agent` sürüm `0.7.0a1` ve import kökü `kaiwen_agent` olarak kaynakta tanımlıdır; alpha API'sı tüketim sırasında pinlenmeli ve yeniden doğrulanmalıdır. Kaiwen Speech'in mevcut Python import kökü `kaiwen_voice` olup GitHub repo adı `kaiwen-speech` ile karıştırılmamalıdır.

### 1.2 Değiştirilmeyecek ürün ilkeleri

1. Normal sohbetin kritik yolunda Agent, ağ, retrieval, harici LLM, scheduler veya onay sistemi **zorunlu değildir**.
2. Local-first çalışma açık bir ürün modudur. Ağ kapalı veya Agent devre dışıyken temel konuşma devam eder; gizli cloud fallback olmaz.
3. Agent yalnız yetkili talep, kayıtlı yetenek ve kullanıcı/policy sınırları içinde çalışır; modelin metni **yetki belgesi değildir**.
4. Sesli komut, doğru kişiden geldiği kanıtlanmış bir kimlik doğrulama yöntemi değildir; mikrofonu duyan başka kişi de konuşabilir.
5. Audio callback, PCM ring buffer ve playback thread'leri Agent beklemez; Python Agent çağrısı kendi asenkron iş kuyruğunda yer alır.
6. Dış eylemler için allowlist, argument validation, onay, idempotency, audit, deadline ve belirsiz sonuç politikası ayrı ayrı uygulanır.
7. Gerçek model kabiliyeti, sahte demo ve text-to-speech köprüsü birbirinin yerine sunulmaz.
8. Mümkün olan en küçük çalışan dikey dilim seçilir; distribüe agent mesh, çoklu ekip, otomatik amaç takibi ve sürekli mikrofon dinleme başlangıç kapsamında değildir.

## 2. Repository sınırları ve sahiplik tablosu

| Repository | Sahip olduğu fonksiyon | Entegrasyon kenarı | Live'da yasaklanan kopyalama |
|---|---|---|---|
| `kaiwen-live` | UI, mikrofon, hoparlör, OS izinleri, sidecar, session/turn, intent ve response sunumu | `LiveAgentBridge` | Agent policy engine veya Speech transformer yeniden yazımı |
| `kaiwen-speech` | Codec/Transformer, konuşma generation, ileride speech control/conditioning | Speech adapter | Agent SDK importu, tool registry, OS mikrofon izni |
| `kaiwen-agent` | Provider routing, tool schemas, policy/approval, jobs, events, memory ve audit | Sürümlü `AgentRuntime` | Live cihaz ve PCM callback iş mantığı |
| `kaiwen-forge` | Model evaluation/release/compatibility | Doğrulanmış Speech artifact | Agent onay kayıtlarının model manifestine taşınması |
| `kaiwen-corpus` | Eğitim verisi, konuşma segmentleri ve izinler | Gelecekte ayrı araştırma dataset'i | Live mikrofonundan izinsiz veri toplama |
| `kaiwen-design` | React tokens, Button, Modal, Toast, Tooltip, Progress, accessible UI | Mevcut UI component paketi | Agent durum makinesinin kütüphane içine alınması |

İki SDK'yı aynı sidecar Python sürecinde kullanmak **zorunlu tasarım kararı değildir**. Agent provider'ı ağır bağımlılık, network veya GPU bütçesi getiriyorsa ayrı local worker/child process tercih edilebilir. Process ayrımı güvenlik ve izolasyona yardım eder ama yetki/policy yerine geçmez. Tek süreçte de iki bağımsız kuyruk ve bounded executor zorunludur. Electron renderer Agent'ın araçlarını doğrudan çağırmaz; bridge'e ancak önceden tanımlanmış semantik eylemleri bildirebilir.

### 2.1 Bağımlılık ve sürüm pinleme

- Live yalnız sürümü ve API sözleşmesi doğrulanmış Agent/Speech paketlerini tüketir; sibling repo varlığı otomatik runtime erişimi anlamına gelmez.
- Agent'ın `AgentRuntime`, `RuntimeIdentity`, `RunMode`, `ToolExecutor` ve speech adapter'larının importları **mevcut**. Örnek `AgentRuntime.chat()`/`action()` kullanılabilir, fakat Live bağlantısı henüz yazılmamıştır.
- `AgentRuntime.run(mode=workflow)` mevcut kaynakta `RuntimeModeUnavailableError` ile reddedilir. Durable workflow bileşenleri bulunması, `.run(workflow)` çağrısının çalıştığı anlamına gelmez.
- Agent'daki Realtime Core ve OpenAI Live sağlayıcıları, Kaiwen Speech native stream'i yerine geçmez; ayrı provider ve ayrı veri politikasıdır.
- Değişen paket adları, eski `kaiwen-agent-platform` metadata URL'leri, alpha API sözleşmeleri ve `kaiwen_voice`/`kaiwen-speech` adlandırması planlı migration kapsamındadır.

## 3. İki yol: Fast Path ve Agent Path

```text
                 Mikrofon → ses çerçeveleri → konuşma turu
                                     │
                       Live Session / Intent Router
                                     │
            ┌────────────────────────┴──────────────────────────┐
            │                                                   │
        FAST PATH                                           AGENT PATH
            │                                                   │
      Kaiwen Speech                                    doğrulanmış intent
     codec → speech LM                                      / kullanıcı UI
      → codec → PCM                                            │
            │                                             izin + bütçe
       Playback queue                                          │
            │                                          AgentRuntime / jobs
         Hoparlör                                            / tools
                                                                │
                                                  Result + provenance + status
                                                                │
                                                    ┌───────────┴───────────┐
                                                 Text UI           Opsiyonel voice
                                                                   adapter / TTS
```

Bu çizimde **Agent Path'in sesten otomatik çıkarıldığı iddia edilmez**. Mevcut Speech modeli kullanıcı sesinden güvenilir komut metni, tool schema veya `agent_requested` token'ı üretmiyor. Hedefte üç tetikleme düzeyi vardır: (A) UI üzerinden açık metin komutu, (B) kullanıcı tarafından etkinleştirilen ayrı STT+intent analiz yolu, (C) gelecekte yalnız eğitim/ölçüm sonrası açılacak modelin özel control token'ları. İlk V1 yalnız A yolunu gerektirir.

### 3.1 Fast Path'in bağımsızlığı

Bir özellik kapalıyken, Agent provider API anahtarı yokken, Ollama başlatılmamışken, DNS çözümlenmezken veya onay modalı gösterilemezken normal Speech çalışmalıdır. Kendi modelinin kötü ses üretmesi ayrı Speech kalite problemidir; Agent eksikliği sebebiyle tüm mikrofon akışı kilitlenmez. Runtime readiness kapıları `speech_ready`, `agent_ready`, `audio_output_ready` olarak bağımsız raporlanır. UI "Agent bağlı değil" derken ses sohbetini kapatmaz.

### 3.2 Agent Path'in motivasyonu ve veri akışı

Kullanıcı "Bugünkü yağış ihtimalini kontrol et" dediğinde Fast Path'in dünya bilgisini biliyormuş gibi uydurması yerine Agent'a açık bir bilgi talebi yönlendirmek mantıklıdır. Fakat bu seçim V1'de yalnız açık UI eylemi veya doğrulanmış intent adapter'ıyla mümkündür. Bir cümlede "kontrol et" geçmesi ağ erişimine izin vermez. Kullanıcının "şu kişiye mesaj gönder" demesi ile mesajın gerçekten gönderilmesi farklı adımlardır; arada kimlik, hedef, içerik, eylem riski ve onay gerekir.

Agent dönen metnin kaynakları, hata durumu, zaman damgası ve varsa tool sonucu birbirine bağlanır. Live sonucu seslendirebiliyorsa, hangi mekanizmayla seslendirildiği (`native_conditioned`, `tts_bridge`) bilinir. Böylece transcript'in görüntülenmesi, sesin sentezlenmesi ve dış görev başarısı üç ayrı gözlemdir.

## 4. İlk dikey dilim ve kabul kriteri

İlk uygulanabilir entegrasyon **"Ajan'a metinle sor"** şeklindedir. Kullanıcı açık bir sekmede "Bir cümlelik açıklama yaz" metnini girer; Live `AgentRuntime.chat` çağrısını background task'a iletir; sabit test modeli veya kurulu gerçek provider sonuç üretir; UI bunu metin olarak gösterir. Herhangi bir dosya/sistem değişikliğine izin verilmez. Speech oturumu aynı anda çalışabiliyorsa kapanmaz.

**Kabul:** (1) Agent kapalıyken normal Speech etkilenmez, (2) `chat` aracı açmaz, (3) iki istek birbiriyle karışmaz, (4) süre aşımı kullanıcıya anlaşılır gösterilir, (5) renderer ham secret/SDK nesnesi görmez, (6) gerekirse kullanıcı Agent çağrısını iptal eder, (7) fake provider sonucu gerçek araştırma/araç çalışması gibi sunulmaz.

Sonraki dilim read-only, açıkça izin verilmiş bir araçtır. İşlem yapan araçlara geçmeden önce durable approval ve idempotency altyapısı takılır. Kullanıcı bir sonucu duyabilsin diye STT/TTS'yi varsayılan olarak tüm sohbetin içine yerleştirmek zorunlu değildir.

## 5. Entegrasyon modları ve feature negotiation

Live sidecar başlangıçta Agent yeteneklerini runtime koşullarına göre bildirir. Derlenmiş TypeScript constant veya UI tercihi tek başına gerçek kapasite sayılmaz.

| Capability | İlk değer | Ne zaman `true` olabilir? | Güvenlik notu |
|---|---:|---|---|
| `agent_text_chat` | `false` | Pinlenmiş Agent SDK ve kurulu text provider testleri geçtiğinde | Tool yok |
| `agent_readonly_tools` | `false` | İzinli en az bir read-only tool, model ve policy test edilince | Veri yerelliği korunur |
| `agent_mutating_tools` | `false` | Approval + durable action intent + idempotency + audit doğrulanınca | Kullanıcı onayı gerekir |
| `agent_background_jobs` | `false` | Job manager/persistence ve restart recovery test edilince | İş ve ses ayrı |
| `agent_audio_intent` | `false` | Gerçek ASR/intent doğruluğu ve açık kullanıcı ayarı olduğunda | Sese güvenerek yetki verme |
| `agent_native_voice_result` | `false` | Speech text conditioning/control model ve kalite testleri hazırsa | Native voice gerçekten ölçülür |
| `agent_tts_voice_result` | `false` | Açıkça kurulmuş yerel TTS adapter + izin + test varsa | Native ile karıştırılmaz |
| `agent_offline_only` | Konfigürasyona bağlı | Tüm yolun ağsız çalıştığı kanıtlanınca | Cloud provider'a fallback yok |

**HEDEF örnek kontrol payload'ı** (gerçek Live endpoint'i değildir):

```json
{
  "schema_name": "kaiwen.live.capabilities",
  "schema_version": "1.0.0",
  "runtime_kind": "local",
  "features": {
    "speech_batch": true,
    "speech_native_streaming": false,
    "agent_text_chat": false,
    "agent_readonly_tools": false,
    "agent_mutating_tools": false,
    "agent_background_jobs": false,
    "agent_audio_intent": false,
    "agent_native_voice_result": false,
    "agent_tts_voice_result": false
  },
  "agent": {
    "sdk_version": null,
    "provider": null,
    "data_locality": "local_only",
    "approval_mode": "manual"
  }
}
```

Bu payload yalnız schema fixture'dır. `speech_batch=true` değeri bile çalışan Live repository'sinin bugünkü durumunu değil, hedef bir konfigürasyonun capability örneğini temsil eder. Capability runtime sağlığı değiştiğinde olayla güncellenir; yeniden bağlandığında client önceki `true` bayraklarını körlemesine kullanmaz.

## 6. Hedef LiveAgentBridge port'u

UI ve Electron sınırı, Agent'ın iç SDK sınıflarını bilmemelidir. Live içinde bir `LiveAgentBridge` interface'i seçilir. Komut sayısı en küçük çalışan akış için sınırlıdır: capability oku, metin isteği başlat, durum sorgula, istek iptal et ve gerekiyorsa onay yanıtı gönder. İlk V1'de uzun süreli job/approval komutları kapalı olabilir.

```python
# HEDEF / PSEUDOCODE — kaiwen-live uygulamasında henüz bulunmayan port.
from dataclasses import dataclass
from typing import Literal, Protocol

@dataclass(frozen=True)
class LiveAgentRequest:
    request_id: str
    session_id: str
    turn_id: str
    generation_id: str | None
    input_text: str
    mode: Literal["chat", "action"]
    allowed_tools: tuple[str, ...]
    locale: str = "tr"

@dataclass(frozen=True)
class LiveAgentResult:
    request_id: str
    run_id: str | None
    status: Literal["completed", "failed", "cancelled", "uncertain"]
    text: str | None
    error_code: str | None

class LiveAgentBridge(Protocol):
    async def submit(self, request: LiveAgentRequest) -> str: ...
    async def get(self, request_id: str) -> LiveAgentResult: ...
    async def cancel(self, request_id: str) -> None: ...
```

`request_id` idempotency için **tek başına** yeterli değildir; aynı kullanıcı ve session kapsamına bağlanır. `generation_id`, yalnız yanıtın ilgili ses generation'ı ile korelasyonudur; agent run ID yerine geçmez. Result `completed` olması, tool çağrılarının hepsinin başarılı olduğu veya üçüncü taraf sistemde etkinin doğrulandığı anlamına gelmez; özellikle eylemlerde ayrı execution receipt gerekir.

### 6.1 Zaman ve sahiplik sınırı

Bridge, UI event loop'una veya gerçek-zamanlı PCM callback'ine `await agent...` sokmaz. Queue sabit kapasitelidir; aşımda açık `AGENT_QUEUE_FULL` hatası döner. Bir session için varsayılan tek aktif mutation run ve sınırlı read-only parallelism önerilir; kesin sınır donanım ve görev profili ölçülerek konur. Agent işinin sahipliği `tenant_id`/`user_id`/`session_id`/`request_id` üzerinden kurulur; cihaz ID'sinden güvenilir kullanıcı kimliği türetilmez.

### 6.2 Adapter içindeki katmanlar

```text
Live renderer
    → typed preload (semantic request only)
    → Electron main (window/session/capability validation)
    → local authenticated sidecar IPC
    → LiveAgentBridge (Live-owned)
       ├─ intent validation & bounded queue
       ├─ trusted identity resolver
       ├─ AgentRuntime adapter (kaiwen-agent)
       ├─ policy/approval/status mapping
       ├─ output presenter + optional TTS adapter
       └─ audit/telemetry adapter (redacted)
```

UI `tool_name` ve keyfi dosya yolu gönderebilirse tool allowlist anlamsızlaşır. Araç seti product config içinde, trusted backend tarafından kurulmalıdır. Bazı güvenilir UI eylemlerinde kullanıcı hangi aracı çağırmak istediğini seçebilir; bu seçimi de allowlist+policy süzgeci belirler. Untrusted model veya web sayfası bu seçimi genişletemez.

## 7. Gerçek Kaiwen Agent SDK'sı ile ilk entegrasyon

Aşağıdaki örnek **Agent kaynak reposunda bulunan API'yı** kullanır; Kaiwen Live'ın kendi bridge'i değildir. Model cevabı deterministik fake'tir; internet, gerçek araç veya gerçek ses gerektirmez. Gerçek kurulum için `kaiwen-agent` sürümü pinlenir.

```python
# MEVCUT AGENT API — provider-free sözleşme örneği.
import asyncio

from kaiwen_agent import AgentRuntime, RuntimeIdentity
from kaiwen_agent.models.fake import FakeModelProvider
from kaiwen_agent.types import ModelResponse

async def main() -> None:
    runtime = AgentRuntime(
        name="live-chat-demo",
        model=FakeModelProvider([ModelResponse(text="Merhaba, bu test yanıtıdır.")]),
    )
    identity = RuntimeIdentity(
        session_id="demo-session",
        tenant_id="local-user",
        user_id="user-1",
        conversation_id="demo-conversation",
        environment="development",
    )
    result = await runtime.chat("Kısa bir yanıt yaz.", identity=identity)
    assert result.status == "completed"
    print(result.text)

if __name__ == "__main__":
    asyncio.run(main())
```

Bu örnek `AgentRuntime.chat()` kullanır; araçlar chat modunda **görünmez**. Bu yüzden ajan fikri "hava durumuna bak" olsa bile gerçek dış veriyi araçla almış olmaz. `action(text, identity=..., tool_names=...)` ayrı, izinli moddur; tool schema, `ToolExecutor`, policy, izinler ve mümkünse ayrı onay kapısı yoksa açılmaz. `workflow` run modu mevcut public facade üzerinde koşulmaz; ileride uygun workflow controller ile ayrıca entegre edilebilir.

### 7.1 Gerçek provider seçimi

- **Local-first** kullanıcı modu yalnız yerelde kurulu ve onaylı provider'a yönlenir. `OllamaChatProvider` gibi adapter'ların mevcut olması, bilgisayarda modelin indirildiğini veya çalıştığını kanıtlamaz.
- Cloud provider seçimi farklı açık kullanıcı ayarı ve veri aktarımı bildirimi gerektirir. Mikrofon/transcript otomatik cloud'a gönderilmez.
- Gizli anahtarlar renderer, React store, localStorage, WebSocket payload veya audit log'a yazılmaz; Windows credential store veya güvenli backend secret provider kullanılır.
- Provider fallback konfigürasyonunda `data_locality` korunur. `local_only` bir oturumda remote failover kabul edilemez.
- Agent'ın cevap üretim zamanı, Speech modelinin TTFA metriğine karıştırılmaz. `agent_wait_ms`, `tool_ms` ve `voice_render_ms` ayrı kaydedilir.

## 8. Niyet tanıma: önce güvenilir eylem, sonra konuşmadan tetikleme

### 8.1 İlk güvenli seçenek: açık UI

Kullanıcı Live içinde ayrı bir "Ajan'a sor" girişi açar. Bu giriş metin isteğinin Agent'a gönderileceğini açıkça gösterir. Kullanıcı metni kendisi girer veya varsa ayrı, açıkça başlatılmış transkripsiyon sonucunu kontrol edip onaylar. Tool eylemi `action` ise uygun onayların Agent tarafında hâlâ uygulanacağı belirtilir. Mikrofonu ilk açma izni, web araması veya dosya erişimi izni değildir.

### 8.2 Ayrı STT + intent adapter (V2)

Sesli Agent komutu istenirse isteğe bağlı ASR, kullanıcı konuşmasını metne dönüştürür; metin ayrı intent classifier/router'da analiz edilir. STT çıktısı hatalı olabileceğinden kullanıcıya kritik parametrelerin önizlemesi sunulur. "Ali'ye mesaj yolla" gibi eylemler kişi adı, hedef adres, içerik ve yan etkinin bütününü açıkça gösteren onay olmadan yapılmaz. Transkripsiyon yalnız `agent_audio_intent` açıkken çalışır, normal Fast Path'e zorla girmez.

Kısa komutlarda intent için üç karar kullanılır: `no_agent`, `propose_agent`, `user_confirmation_required`. Düşük güven skoru `no_agent` veya düzeltme isteği doğurabilir; yüksek güven skoru **otomatik eylem izni değildir**. Kullanıcı sessizce dinleniyorken çevrede geçen bir emir, Live'ın araç çağırması için yeterli değildir.

### 8.3 Model kontrol token'ları (araştırma)

İleride Speech Transformer özel `AGENT_QUERY`, `AGENT_RESULT`, `AGENT_CANCEL` benzeri semboller üretecek şekilde veri ve loss tasarımıyla eğitilebilir. Bugün böyle public inference API'si, güvenilir tanıma kalitesi veya modelden çıkan tool argument şeması **mevcut değil**. Bu sözleşme ancak Speech tarafında token ID tahsisi, codec-vocab çakışma testi, tokenizer/checkpoint migration, inference output türü, labeled dataset ve eval ölçümleriyle açılır. Tek bir özel tokenın varlığı tool çağrısını yetkilendirmez; Live yine ürün policy'sini ve Agent approval'ını uygular.

### 8.4 Sesli komut ve yan yana konuşma

Bir odadaki televizyondan "hesapları sil" cümlesi duyulabilir. V1 sesli intent açık olsa bile kime ait olduğu doğrulanmamış ses, etkili araçları otomatik çalıştırmamalıdır. Wake word desteği ileride eklenirse bunun yetki ya da kimlik doğrulaması olmadığı açıklanır. Speaker diarization cihazı önündeki kişinin hesap sahibi olduğunu kanıtlamaz. Kritik eylemde güvenilir kullanıcı etkileşimi (UI onayı/OS mekanizması) istenir.

## 9. İstek envelope'ı: UI mesajı ile Agent SDK argümanını ayır

Live kontrol düzleminde sürümlü, küçük JSON payload kullanılır. Aşağıdaki **HEDEF** mesaj, Electron→sidecar semantik kontrol örneğidir; doğrudan `AgentRuntime.run` parametresi değildir:

```json
{
  "protocol_name": "kaiwen.live.session",
  "protocol_version": "1.0.0",
  "event_id": "evt-agent-request-0001",
  "session_id": "session-demo-1",
  "stream_id": "agent-control",
  "sequence": 14,
  "event_type": "agent.requested",
  "occurred_at_utc": "2026-10-30T15:00:00Z",
  "monotonic_ns": 100000000,
  "correlation_id": "corr-agent-0001",
  "payload": {
    "request_id": "agent-req-0001",
    "turn_id": "turn-7",
    "generation_id": "gen-9",
    "session_epoch": 3,
    "input_modality": "text_ui",
    "input_text": "Bir cümlede CDN nedir açıkla.",
    "desired_output": "text",
    "locale": "tr",
    "requested_capability": "agent_text_chat"
  }
}
```

`tenant_id` ve `user_id` gibi güvenilir kimlikler renderer'ın keyfi beyanından alınmaz; backend session principal'ından atanır. `requested_capability` bir **istek**tir, izin kararı değildir. `occurred_at_utc` gösterim ve korelasyon için; performans ölçümünde aynı clock kaynağından monotonic timestamp kullanılır. `sequence` ilgili stream içinde artar. `session_epoch` yeniden oluşturulan session'a ait eski yanıtların karışmasını engellemede yardımcıdır.

### 9.1 Validasyon tablosu

| Alan | Kural | Hata |
|---|---|---|
| `protocol_version` | Ortak destek aralığında | `AGENT_PROTOCOL_INCOMPATIBLE` |
| `session_id` | Yetkili açık oturum | `AGENT_SESSION_INVALID` |
| `request_id` | Owner scope içinde benzersiz/idempotent | `AGENT_REQUEST_CONFLICT` |
| `turn_id` | Session'da bilinen tur | `AGENT_TURN_INVALID` |
| `input_text` | Unicode, boyut ve içerik sınırlı; boş olamaz | `AGENT_INPUT_INVALID` |
| `requested_capability` | Backend allowlist / negotiation | `AGENT_CAPABILITY_DISABLED` |
| `desired_output` | `text`, `voice_if_available` gibi açık enum | `AGENT_OUTPUT_UNAVAILABLE` |
| `deadline` | Bounded, monotonic ve profille uyumlu | `AGENT_DEADLINE_INVALID` |

JSON schema'sı TypeScript ve Python için tek kaynaktan türetilir; frontend tipi ile Python modelini elle kopyalayıp sürüklenmeye bırakma. Decode edilen payload bilinen alan/enum doğrulamasından geçer. Kişisel transcript ve tool argument içeren mesajlar debug log'larında bütün hâliyle yazılmaz.

## 10. Kimlik modeli ve permission intersection

Agent SDK'sının `RuntimeIdentity` nesnesi `session_id`, `tenant_id`, `user_id`, `conversation_id`, `client_id`, `trace_id`, `environment`, `permissions` ve `metadata` taşır. Live güvenilir principal kaynağını (yerel Windows profili + app session) tanımlar. `local_user` varsayılan kimliği sadece tek kullanıcı senaryosunun bileşenidir; başka local process'in otomatik güvenilir kullanıcı olduğunu ispatlamaz.

**Etkili izin kümesi** aşağıdaki kümelerin kesişimidir:

```text
host_product_allowlist
∩ explicit_user_grants
∩ runtime_workspace_profile
∩ agent_definition_permissions
∩ tool_definition_permissions
∩ per_request_policy
∩ data_locality_constraints
```

Çarpıcı bir sonuç: Kullanıcının "bu görevi yap" demesi, konuşmanın transkripti veya bir modelin `tool_calls` listesi bu kümelere yeni yetki eklemez. İstemci "allowed_tools": ["filesystem.delete"] gönderirse ürün konfigurasyonunda böyle bir izin yoksa istek reddedilir. Read-only görevler bile erişimi kısıtlı klasöre veya mahrem e-postaya otomatik erişemez.

### 10.1 İzin katmanları

- **Mikrofon izni:** Sesi yakalamak içindir; Agent tool izni değildir.
- **Sesin Agent'a aktarım izni:** Ayrı STT ve provider kullanılıyorsa hangi verinin nereye gideceği açık olmalıdır.
- **Tool capability:** Belirli servise okuma/yazma yetkisi, duration ve scope ile sınırlanır.
- **İşlem onayı:** Belirli argüman fingerprint'i, tool ve run'a bağlı tekil karardır.
- **Kalıcı bellek izni:** Konuşma veya transcript'i daha sonra kullanılacak hafızaya alma ayrı politikadır.
- **Bulut veri izni:** Yerel-only politikasından açık geçiş gerektirir; genel "Agent açık" seçimi yerine geçmez.

### 10.2 Güvenilir context üretimi

Live `RuntimeIdentity`'yi backend içinde oluşturur. `trace_id` ve kullanıcı kimliği sunucudan gelir; istemcinin verdiği rastgele `tenant_id` doğrudan kullanılmaz. Session/turn korelasyonu `metadata` içinde taşınabilir, fakat bu metadata'nın model tarafından talimat gibi okunmamasına dikkat edilir. `permissions` default boş; sadece gerekli capability set edilir. Her run sonrasında kesin izinler audit'e aktarılır; secret değerleri aktarılmaz.

## 11. Chat, action ve workflow sınırı

Kaiwen Agent'ın gerçek `AgentRuntime` API'sinde:

- `chat(text, *, identity=...)` **araçları görünmez** kılar; kısa metin yanıtı için uygun.
- `action(text, *, identity=..., tool_names=[...])` belirlenmiş araçları seçer ve Agent'ın `ToolExecutor` yoluna gönderir; policy/approval burada merkezi kalır.
- `run(..., mode=RunMode.WORKFLOW)` bu sürümde `RuntimeModeUnavailableError` fırlatır; bu yol Live MVP'nin parçası değildir.
- Agent'da ayrı `JobManager`, `WorkflowController`, `TextJobBridge` vb. bileşenlerin varlığı, bunların Live'a otomatik entegre olduğunu göstermez.

**Hedef çağrı seçimi:** `requested_capability=agent_text_chat` → `chat` ve boş tool set. `agent_readonly_tools`/`agent_mutating_tools` → yalnız backend tarafından seçilmiş `action`, tool policy ve validation. Uzun görev gerekiyorsa JobManager'a host kontrolüyle devredilir; ne AudioCallback ne React Promise zinciri job sahibi olur.

### 11.1 Read-only demek sıfır risk değildir

Arama, not okuma, dosya görüntüleme gibi araçlar sistemde değişiklik yapmayabilir ama gizli bilgi açıklayabilir. Arama snippet'i güvenilmez bir prompt injection taşıyabilir; MCP şema discovery'si yetki vermez. Read-only eylem sonuçları da kaynak, izin, veri yerelliği ve sonuç boyutu kısıtlarına tabidir. ``read`` yetkisi bütün kullanıcı dizinlerine erişim anlamına gelmez.

### 11.2 Mutating action'ın zorunlu kapıları

Yan etkili tool çalışmadan önce: schema validation, güvenilir owner, policy allow, approval gate, argument checksum, durable action intent, idempotency identity ve audit etkin olmalı. Bütün kapılar tamamlanmazsa ilgili capability kapalı tutulur. Yalnız UI'da bir "Onayla" düğmesi göstermek, Agent'ın approval mekanizmasına bağlanmamışsa **gerçek yetkilendirme değildir**.

## 12. Yan etkili tool'lar için onay protokolü

Live, Agent'ın `ApprovalRequest`/durable gate mekanizmasını ürünün görünür onay ekranına adapte eder. Girişteki `arguments` ve action intent ID yetkili backend'den alınır; UI bunları sessizce değiştirerek farklı aksiyona onay veremez. Ekran en az şunları gösterir:

| Alan | Kullanıcıya gösterilecek içerik |
|---|---|
| Eylem | Tam tool amacı; ör. "Dosyaya metin yaz" |
| Hedef | Seçilmiş dosya/klasör/hesap ve beklenen etki |
| İçerik | Gönderilecek mesaj/yazılacak değişiklik özeti |
| Etki | Okuma, geri alınabilir yazma, silme/geri döndürülemez |
| Belirsizlik | Offline/online, gecikme, olası ücret, ek servis riski |
| Seçimler | **Onayla** / **Reddet** / gerektiğinde **Düzenle ve tekrar doğrula** |

Düzenleme, mevcut onay fingerprint'ini geçersiz kılar; düzeltilmiş argümanlar için yeni policy/approval gerekir. Onay zaman aşımına uğrarsa **reddetme yönünde** davranılır. Session kapanışı, farklı kullanıcı girişi veya app yeniden başlatma eski modal onayını otomatik devam ettirmez. Side-effecting işlem devam ederken kullanıcı "Sustur" derse yalnız playback durur; işin iptal edilmesi ayrıca istenir.

### 12.1 Onay isteği örneği

```json
{
  "schema_name": "kaiwen.live.agent_approval",
  "schema_version": "1.0.0",
  "request_id": "agent-req-0012",
  "run_id": "run-demo-09",
  "approval_id": "approval-demo-004",
  "action_intent_id": "intent-demo-004",
  "tool_name": "workspace.write_note",
  "side_effect": "reversible",
  "arguments_checksum": "sha256:example-hash-to-be-replaced-by-real-digest",
  "summary": "Seçili notun sonuna bir paragraf eklenecek.",
  "target_label": "Proje notları / toplantı.md",
  "expires_at_utc": "2026-10-30T15:05:00Z",
  "decision": "pending"
}
```

Bu örnek biçim şeması **hedef**tir. Gerçek checksum burada örnek metindir, geçerli SHA-256 değildir. Üretim doğrulayıcısı gerçek hexdigest biçimini ve kaynak kaydıyla eşleşmesini denetler. Onay sonucu `approved`/`denied` şeklinde backend'e güvenli kanal üzerinden gider ve tekil kapsamda tüketilir. Tool ve target adı gösterim amaçlı olabilir; yetkilendirilen gerçek schema argümanları server tarafında kilitlenir.

### 12.2 Kullanıcı eylemi vs Agent policy

Kullanıcı modalda onay verse dahi Agent runtime izin vermeyen tool'u çalıştıramaz. UI onayının varlığı capability setini yükseltmez. Policy onay istiyor fakat modal açılamıyorsa işlem **çalışmamalıdır**. Başka bir run'daki onay yeniden kullanılamaz. Tek onay birden fazla işlem veya alıcı için zincirleme kullanılamaz. "Bir kez izin verdim, bundan sonra her seferinde yap" modu ilk V1 kapsamı dışındadır.

## 13. Idempotency, dayanıklılık ve belirsiz sonuç

Yan etkili bir tool'un timeout olması, dış servisin işlemi gerçekleştirmediğini kanıtlamaz. E-posta gönderildikten sonra cevap paketinin kaybolması mümkündür. Bu yüzden timeout sonrası aynı işlemi otomatik tekrar çağırmak çift gönderim riski yaratır. Kaiwen Agent'daki `ActionIntentStore`, `DurableApprovalStore` ve `ToolExecutor` bu problemin çekirdek mekanizmalarını içerir; host bunları **uygun dayanıklı store ve ürün kimliğiyle bağlamadan** "crash safe" diyemez.

Olası durumlar: `prepared`, `executing`, `succeeded`, `failed`, `cancelled`, `uncertain`. `uncertain`, kullanıcıya kesin başarısızlık veya başarı değil, kontrol gerektiren sonuç olarak gösterilir. İşlem tamamlanmış görünüyorsa kanıt olarak işlem receipt'i alınır. Sistem kendisini yeniden başlattığında belirsiz işlem için otomatik retry açılmaz; reconciliation ve kullanıcıya açık durum sağlanır.

### 13.1 Request ve tool idempotency farkı

- Live `request_id`: aynı UI isteğinin iki kez submit edilmesini sınırlar.
- Agent `run_id`: model/tool yürütme ve event'lerin kaynağıdır.
- Tool `call_id`: modelin tek bir tool çağrısıdır.
- Tool `idempotency_key`: gerçek harici eylemin tekrarını kontrol eder.
- `action_intent_id`: durable side-effect yaşam döngüsünün kimliğidir.

Birini ötekine eşitlemek yanlış. Aynı kullanıcı metni iki kez gönderebilir, bu iki ayrı request olabilir. Aynı request'ın network retry'si ise ikinci action'a dönüşmemelidir. Checksum'a token/secret yazılmaz; güvenilir canonicalization uygulanır.

## 14. Agent görevleri ve asenkron işlem modeli

Agent Path'in süresi normal konuşma yanıtından uzun olabilir. Arama, birkaç kaynaktan bilgi toplama, dosya okuma veya kalıcı job saniyeler/dakikalar sürebilir. Bu süre boyunca kullanıcının mikrofonu kapatılması gerekmez. Job durumu ve PCM pipeline'ı ayrı mekanizmalarla ilerler.

### 14.1 Önerilen durum makinesi

```text
created
   ↓ validate + authorize
queued ─────────────→ rejected
   ↓ worker admitted
running ────────────→ failed
   ├── needs_approval ─→ approved ─→ running
   │                   ├→ denied ─→ cancelled/failed
   │                   └→ expired → cancelled/failed
   ├── waiting_external ─→ running
   ├── cancel_requested ─→ cancelled | uncertain
   └── completed (verified response and optional receipts)
```

Durum adları **Live'ın hedef görünümüdür**, Agent'ın tüm mevcut internal enum'larıyla birebir aynı değildir. Adapter mapping tablosu sürümlenir. `completed` yalnız run'ın tamamlandığını anlatır; bir cevapta "yapıldı" yazması yeterli değildir. Terminal durumlar tekrar `running`e dönmez; yeni deneme yeni attempt ID alır.

### 14.2 İş sahibi ve lifecycle

- Session kapanırsa read-only ephemeral Agent isteği iptal edilebilir; kalıcı job sadece açık ürün politikası varsa devam edebilir.
- `stop_playback` hiçbir zaman doğrudan job cancellation değildir.
- `cancel_generation`, Speech'ün o ses üretimini durdurur; Agent tool veya işini durdurmaz.
- `cancel_agent_request`, uygun scope'ta Agent çağrısına cancellation bildirir.
- `cancel_agent_job`, mevcut JobManager sözleşmesine göre iptal ister; dış serviste çoktan yapılan etkiyi geri almaz.
- `close_session`, yeni event'leri UI'ya kapatır; durable job'lar için explicit ownership policy gerekir.

### 14.3 Timeout ve deadline sınıfları

`input_intent_timeout`, `agent_queue_timeout`, `agent_provider_timeout`, `tool_timeout`, `approval_timeout`, `job_max_lifetime`, `voice_renderer_timeout` bağımsızdır. Tek bir belirsiz "5 saniye timeout" bütün aşamalar için kullanılmaz. İlk değerler araştırma varsayımı olabilir; gerçek donanım ve provider sonuçlarıyla test edilir. Deadline monotonic clock üzerinden kontrol edilir; UTC yalnız denetim kaydı ve UI için kullanılır.

## 15. Konuşma turu, session, job ve event korelasyonu

Her Agent isteği bir kullanıcı turuna bağlanabilir; ancak o turun ses üretiminden bağımsız yaşayabilir. Live'da asıl ses session kimliği `session_id` ve `session_epoch`'tur. Her kullanıcı konuşması bir `turn_id`, her Speech üretimi `generation_id`, her Agent isteği `request_id`, Agent SDK çalıştırması `run_id` ve tek tool çağrısı `call_id` alır. Bu kimlikleri bir tek GUID altında toplamak, barge-in ile tool completion'ın karışmasına yol açar.

| Kimlik | Sorumlusu | Ömür | Hangi sınırda kullanılır? |
|---|---|---|---|
| `session_id` | Live session supervisor | Oturum | Ses, UI ve Agent isteklerini bağlamak |
| `session_epoch` | Live | Her session yeniden başlatma | Eski session event'lerini reddetmek |
| `turn_id` | Live konuşma yönetimi | Bir kullanıcı turu | Intent bağlamı, transcript/provenance |
| `generation_id` | Speech/Live adapter | Tek sesli yanıt | Stale PCM temizleme ve barge-in |
| `request_id` | LiveAgentBridge | Bir Agent isteği | Dedup, status ve UI |
| `run_id` | Kaiwen Agent | Tek runtime çalıştırması | Tool, approval, audit ve maliyet |
| `job_id` | Agent jobs | Uzun görev | Durum, resume, cancel |
| `tool_call_id` | Agent runtime | Bir araç çağrısı | Onay ve execution receipt |
| `correlation_id` | Güvenilir Live transport | İzleme zinciri | Redacted diagnostics |

### 15.1 Stale result kuralı

Kullanıcı bir şey sordu; Agent 15 saniye çalıştı; kullanıcı o sırada yeni bir konuya geçti. Bu durumda Agent'ın eski sonucu yeni konuşmanın aktif yanıtı gibi otomatik seslendirilmez. Sonuç, sahibi olan `request_id` ve asıl `turn_id` altında "Önceki görevin sonucu" olarak gösterilebilir. Oturum/epoch kapanmışsa UI delivery reddedilir veya kullanıcı açıkça geçmiş görevlere gider; mutating action'ın dış etkisi ise ayrıca reconciliation ister. Bu kural, eski generation PCM'sini reddetmeye benzer ama **aynı değildir**: PCM kuyruktan düşürülebilirken kalıcı iş sonucu audit'ten silinmez.

### 15.2 Aynı anda birden çok istek

Read-only Agent soruları gerekirse eşzamanlı ilerleyebilir; ancak düşük VRAM ve düşük gecikme hedefi nedeniyle concurrency sınırı donanım profilinden gelir. Arka arkaya aynı UI düğmesine basılması aynı request tekrarını üretmez. Kullanıcı farklı iki komut verirse her ikisi ayrı `request_id` ile kaydedilir. UI active card seçili olabilir; sonuçların sırası tamamlanma zamanına göre değişse de semantic ordering ve kimlik karışmaz. Mutating işler için başlangıçta tek aktif intent tavsiye edilir; gerçek kararlılık testleri olmadan paralel yazma işlemleri açılmaz.

## 16. Agent event → Live UI mapping

Kaiwen Agent'ın `AgentEvent` yaşam döngüsü (`run.started`, `run.status`, `tool.started`, `tool.completed`, `approval.requested`, `run.completed`, `run.failed` gibi) Live'a uyarlanır. Bunlar her durumda doğrudan UI event'i değildir. Live örneğin `tool.completed` görüp otomatik "Görev tamamlandı" dememelidir; Agent hâlâ başka tool veya model adımı çalıştırıyor olabilir. Event akışı untrusted payload alanlarını sanitize eder. Kullanıcıya gösterilen her durum, açık bir state transition ve event provenance taşır.

| Kaynak sinyali | Hedef Live görünümü | Açıklama |
|---|---|---|
| `run.started` | `agent_running` | İstek kabul edildi; henüz sonuç yok |
| `run.status` | `agent_progress` | Token usage veya kısa adım bilgisi; söz verilmiş yüzde değil |
| `tool.started` | `agent_tool_running` | Kayıtlı araç başladı |
| `approval.requested` | `agent_awaiting_approval` | UI onay kapısı; execution henüz başlamadı |
| `approval.resolved` | `agent_processing` / `agent_denied` | Kaynaktan doğrulanmış sonuç |
| `tool.completed` | `agent_tool_succeeded` | İlgili tek tool sonucu |
| `run.completed` | `agent_completed` | Agent yanıtı hazır; kaynak etkisi ayrıca doğrulanabilir |
| `run.failed` | `agent_failed` | İspatlanmış hata; uydurma yanıt yok |
| cancel acknowledgement | `agent_cancelled` / `agent_uncertain` | İptalin etkisi açıkça belirlenir |

Unknown event type gelirse `AgentEvent` atılmaz demek yerine sürüm uyumsuzluğu telemetrisi yazılır; kullanıcıya yanlış tamamlanma gösterilmez. Event kuyruğu sınırlanır; token-by-token debug telemetry yüksek hacim oluşturursa örneklenir. Approval ve terminal event'ler drop politikasında öncelikli; açıklayıcı progress gibi coalescable olaylar birleştirilebilir. Durum terminale geçtiğinde geç gelen `progress` tekrar canlı duruma dönüştüremez.

### 16.1 Hedef event örneği

```json
{
  "protocol_name": "kaiwen.live.session",
  "protocol_version": "1.0.0",
  "event_id": "evt-agent-completed-001",
  "session_id": "session-demo-1",
  "stream_id": "agent-control",
  "sequence": 15,
  "event_type": "agent.completed",
  "occurred_at_utc": "2026-10-30T15:00:02Z",
  "monotonic_ns": 2500000000,
  "correlation_id": "corr-agent-0001",
  "payload": {
    "request_id": "agent-req-0001",
    "run_id": "run-demo-01",
    "turn_id": "turn-7",
    "session_epoch": 3,
    "result_modality": "text",
    "text": "CDN, içeriği kullanıcıya yakın sunuculardan ulaştıran dağıtım ağıdır.",
    "source_mode": "fake_fixture",
    "speech_rendering": "none",
    "verified_external_action": false
  }
}
```

`source_mode=fake_fixture` olmasına karşın doğal Türkçe bir cevap örneklemek amacıyla verilmiştir; gerçek Agent araştırması veya canlı internet sorgusu kanıtı değildir. Üretimde özel konuşma metni default loglanmaz; bu JSON yalnız contract fixture/test dosyasına girebilir.

## 17. Agent yanıtının Speech sistemine geri dönmesi

**Bu projenin en önemli açık teknik problemi:** Kaiwen Speech bugün ses tokenlarını girdi ve çıktı olarak işleyen temel inference yoluna sahip; genel amaçlı metinden koşullandırılmış Türkçe konuşma üretimini sağlayan güvenilir public TTS veya `respond_to_text` API'si tanımlı değildir. Bu nedenle `AgentResult.text` bir `SpeechTransformer.generate` içine metin string'i olarak verilemez. Sadece kodek meta verilerinin eşleşmesi, metnin doğal sese çevrilmesi için yeterli değildir.

### 17.1 A seçeneği — Metin olarak gösterim (ilk V1)

Agent tamamlanınca cevap Live'da bir kartta gösterilir. Kullanıcı isterse metni kopyalayabilir, kaynak veya tool sonucunu inceleyebilir. Ana speech-native konuşma Fast Path'te değişmeden sürer. Bu seçenek sesli Agent cevabı vaat etmez; tek çalışan Agent entegrasyonunu hızlı ve doğrulanabilir kılar. UI, işin onay veya bekleme durumunu açıkça gösterir. Agent provider offline ise "Cevap alınamadı" der; modelin kendi sesli tahminini onaylanmış araç sonucu gibi sunmaz.

### 17.2 B seçeneği — Ayrı yerel TTS köprüsü

Kullanıcı açıkça sesli Agent sonucu ister ve uygun TTS motoru yerelde gerçekten kuruluysa, `AgentResult.text` bu motorun doğrulanmış `synthesize(text, voice, language)` arabirimine verilebilir. Çıktı PCM/WAV, Live'ın audio output pipeline'ına **yeni bir generation ve kaynağı belirten etiketle** girer. Bu, "speech-native tek model" değil, **Agent → TTS** hibrit yoludur. Düşük VRAM hedefi varsa TTS ile Speech'in eşzamanlı belleği ölçülür; aynı 2 GB sınırında çalıştığı otomatik varsayılmaz.

TTS için en az: Türkçe telaffuz, sayılar ve kısaltmalar, sample rate, prosodi, streaming destek durumu, model lisansı, offline çalışma, CPU fallback, başlatma maliyeti, PCM chunk zamanları ve iptal davranışı test edilir. Kullanıcıya "Yerel seslendirme" gibi dürüst mod tanımı gösterilir. TTS sesinin PCM çıkarması, Speech Transformer'ın native incremental streaming kullandığını kanıtlamaz.

### 17.3 C seçeneği — Öğrenilmiş Speech conditioning (araştırma)

Speech tarafında modelin Agent sonucunu metin tokenları veya özel conditioning temsilinden alıp kendi codec codebook'larıyla ses üretmesi istenir. Bu yol için metin/audio hizalama verisi, Türkçe seslendirme veri seti, token şeması, eğitim loss'u, inference API'si, codec/version uyumluluğu ve güvenilir konuşma kalitesi gerekir. Önce Speech'te araştırma deneyi; sonra API sözleşmesi; en son Live adapter uygulanır. Aksi hâlde `AgentResult.text` için "model bunu zaten bilir" yaklaşımı gerçek bir çözüm değildir.

### 17.4 Dördüncü kategori: Agent'ın kendi SpeechPipeline örneği

Kaiwen Agent paketinde gerçekten `SpeechPipeline`, `FakeSpeechRecognizer`, `FakeSpeechSynthesizer` ve ilgili port'lar vardır. Kaynak örneği **STT → text handler → TTS** ve açık `audio_processing_allowed=True` izni üzerine kuruludur. Bu araç, Agent'a ayrı bir ses köprüsü göstermek için referans olabilir; **Kaiwen Speech'in native speech-to-speech yapısının yerine geçmemelidir**. `FakeSpeechSynthesizer` ile üretilen bytes gerçek Türkçe konuşma değildir. Ürün diagnostik ekranında hangi yolun kullanıldığı açıkça görülebilir olmalıdır.

### 17.5 Sonuç → Audio transport sınırı

Agent'ın ürettiği metin ve TTS PCM ayrı payload tipleridir. Metin IPC JSON ile taşınabilir; PCM binary frame ve bounded playback queue ile taşınır. UI, metin event'i geldikten sonra ses çalındığını varsaymaz. "Seslendirme başlatıldı", "ilk PCM oluştu", "ilk örnek OS cihazına gönderildi" ve "oynatma tamamlandı" farklı olaylardır. Eskimiş `session_epoch` veya `generation_id` ile gelen TTS chunk, tıpkı Speech PCM gibi hoparlör kuyruğunda reddedilir.

## 18. Sesle geri bildirim: doğal diyalog ve kullanıcı beklentisi

Normal konuşmada Kaiwen Speech kısa duraksamalar, backchanneling ve konuşma ritmini kendisi öğrenmelidir. Agent Path'te ise uzun bekleme olabilir. Kullanıcıya "Araştırıyorum" veya "İzin gerekiyor" gibi geri bildirim verebilmek için **gerçek duruma bağlı** kısa UI metni kullanılabilir. İleride sesli ara bildirim istenirse sadece doğrulanmış TTS/cached, açık kaynaklı veya kullanıcıya ait ses klipleriyle yapılır; dış sistemin sonucunu önceden biliyormuş gibi cümle üretilmez. Kaydedilmiş asistan anonsları varsa hangi asset'in çaldığı telemetry'de görülebilir.

Bekleme sırasında sessizliği sonsuz bir spinner ile kapatmak yerine: neyin beklendiği, beklenen izin, işten ayrılabilme ve iptal seçeneği görünür olmalıdır. Kullanıcı bir yandan yeni doğal sohbet başlatabilir. Agent tamamlandığında mevcut konuşmayı zorla bölerek okumak yerine, **sonuç hazır** bildirimi ve isteğe bağlı dinletme sunulabilir. Kullanıcı yeni bir başlık üzerindeyse eski sonucu otomatik seslendirme varsayılan olarak kapalı tutulur.

### 18.1 Duplex ve echo yönetimi

Gelecekte Agent sonucunu konuşurken dinleyen mikrofon kendi hoparlör çıktısını yeniden intent sanabilir. Echo cancellation, VAD, konuşmacı ayrımı ve barge-in politika ayrı incelenir. İlk güvenilir yöntem gerekirse half-duplex/PTT ve kullanıcı onaylı seslendirmedir. Full-duplex, kullanıcıyı dinleme izni verildiği için kendiliğinden açılmaz. TTS çalarken ikinci bir Agent eylemi otomatik başlamamalıdır; echo ve playback loop testleri bunu kanıtlar.

## 19. Konuşmanın kesilmesi, Agent iptali ve restart

**Ayrı komut sözleşmesi:**

| Komut | Etkisi | Yapmadığı şey |
|---|---|---|
| `stop_playback` | Çıkış tamponunu susturur/temizler | Dış işlemi geri almaz |
| `cancel_generation` | Speech veya TTS ses generation'ını iptal eder | Agent job'ını iptal etmez |
| `stop_microphone` | Yeni ses yakalamayı durdurur | Çalışan Agent provider'ını susturmaz |
| `cancel_agent_request` | Tek Agent request iptalini ister | Harici side effect kesin iptal edildi demek değildir |
| `cancel_agent_job` | Dayanıklı job iptalini ister | `executing`/`uncertain` etkiyi geri almaz |
| `close_session` | Live session'ı kapatır, session kaynaklarını temizler | Açık politikası olmayan durable işi sahiplenmez |
| `revoke_tool_grant` | Gelecekteki tool yetkisini geri çeker | Daha önce tamamlanmış işlemi otomatik geri almaz |

UI "Konuşmayı durdur" düğmesine bastığında ayrı Agent işi mevcutsa görünür şekilde devam ediyor olabilir. Başka bir ürün politikası **"Sesi ve araştırmayı birlikte durdur"** gibi birleşik eylem tanımlayabilir; bu birleşik eylem iç çağrılarını ve kesin/başarısız iptal sonuçlarını ayrı raporlar. `asyncio.Task.cancel()` çağrısının yapılması dış dünyada mutating tool sonucunu garanti etmez.

### 19.1 Kullanıcının çıkışına rağmen devam eden işler

İlk V1'de ephemeral `chat` isteği uygulama kapanınca iptal edilebilir. Kalıcı job desteği daha sonra açılırsa kullanıcıya "Uygulama kapansa da işlem devam edebilir" uyarısı, sonlandırma politikası ve geçmiş işler görünümü gerekir. Kullanıcı uygulamayı açtığında bekleyen approval varsa auth ve sürüm doğrulaması olmadan yeni kullanıcıya gösterilmez. Agent process çöküp restart olursa memory-only store'daki durumlar güvenilir kurtarılabilir sayılmaz. Dayanıklı action intent/approval store entegrasyonunun nasıl yapıldığı test edilmelidir.

### 19.2 Uygunsuz otomatik tekrar örneği

`POST /send_email` isteği timeout verdi; Agent tarafında `uncertain` oluştu. Live "İşlem başarısız, tekrar deniyorum" diyerek aynı tool'u otomatik çağırmamalıdır. Önce sağlayıcının izin verdiği receipt/idempotency veya güvenilir işlem sorgusu yapılır. Sağlayıcı kesin bilgi sunmuyorsa UI sonucu **belirsiz** bildirir, kullanıcıya kontrollü seçenek verir. E-posta gibi işlemlerde yarım kalan konuşmayı yeniden başlatmak da otomatik ikinci gönderim tetiklememelidir.

## 20. Güvenilmeyen içerik ve prompt injection savunması

Agent'ın okuduğu web sayfaları, dosyalar, e-postalar, MCP açıklamaları, tool çıktıları ve transcript içerikleri **veridir, talimat değil**. Kaynak metnindeki "tüm güvenlik kontrollerini kapat" veya "ek tool kaydet" gibi cümleler backend policy'yi değiştiremez. Prompt injection, metinsel bir model çıktısına dönüşmüş olsa bile `permissions`, `tool_names`, `tenant_id`, `user_id` ve approval hakkında yetkili değildir.

**Kontroller:**

1. Tool schemas trusted host tarafından kayıtlıdır; MCP discovery yalnız açıklayıcıdır.
2. MCP tool kullanımı exact schema binding, allowlist, policy ve ToolExecutor üzerinden yapılır.
3. System/policy/secret içeriği retrieval sonuçlarına karıştırılmaz; text context kaynakları provenance ile ayrılır.
4. Read-only output boyutu sınırlanır; büyük belgeler bounded artifact/reference'a indirgenir.
5. Dosya yolu canonicalization ve symlink escape kontrolleri Agent'ın ilgili adapter'ında uygulanır.
6. İsteğin onay gerektirip gerektirmediğini internet sayfası veya model kendi başına değiştiremez.
7. Modelin "gerekirse yönetici olarak aç" önerisi doğrudan Windows elevation/PowerShell komutuna çevrilmez.
8. Agent sonucu UI'da HTML olarak render edilecekse escaping/sanitization ve link güvenliği sağlanır; raw Markdown'dan script çalıştırılmaz.
9. Her tool çağrısı server-side authorization ve audit ile kanıtlanır.
10. En az bir gerçekçi malicious search-result/prompt-injection fixture CI'da denenir.

Bu çerçeve, her kötü içerik saldırısını engellediğimiz iddiası değildir. Hedef, güvenilmeyen metnin ayrı yetki katmanını sessizce aşamaması ve bir regresyon testinde yakalanabilmesidir.

## 21. Hassas veriler, ses mahremiyeti ve veri yerelliği

V1 yerel sesli sohbet, mikrofonu açmak için OS izni kullanır. Ses bu izinden dolayı otomatik olarak Agent'a, internete veya kalıcı diske gönderilmez. Ayrı Agent STT adapter'ı çalışacaksa ses işleme yetkisinin kapsamı ve sağlayıcının yerelliği kullanıcıya açıklanır. Kısa bir transkript bile kişisel veri içerebilir. Varsayılan olarak ham ses, transkript, üçüncü taraf API yanıtı ve tool argümanları debug log'una kaydedilmez.

### 21.1 Veri kategorilerine göre politika

| Veri | Varsayılan | Açık izin varsa | Saklama/erişim |
|---|---|---|---|
| Ham mikrofon PCM | RAM'de geçici | Kullanıcı açık kaydederse | Süre, şifreleme ve silme sözleşmesi |
| Geçici ASR transcript | İşlem için bellek | Kullanıcı not/geçmiş özelliğini açarsa | Hassas içerik redaksiyonu |
| Agent isteği metni | Gerekli en az veri | İlgili provider'a gönderim | Local-only modda cloud yasak |
| Tool argümanı | Trusted backend | Gerekli tool için geçerli scope | Log'da secret maskeleme |
| Secret/token | OS store / secret provider | Araç erişiminde kısa süreli açma | Renderer erişimi yok |
| Agent sonuç özeti | UI'da görünür | Kullanıcı geçmişte saklamak isterse | Retention, silme, export |
| Audit/receipt | Güvenli kimlik ve olay özeti | Denetim için gerekli alanlar | Hassas veri en aza indirilir |
| Telemetry | Sayısal, anonimleştirilmiş | Geliştirme amaçlı açık ek izin | Ses dosyası değil metrik |

### 21.2 Local-only mod

`data_locality=local_only` oturumunda izin verilen sağlayıcılar ve tool'lar gerçekten ağsız çalışabilir olmalıdır. MCP remote servis, bulut LLM ve online web search bu modda otomatik devreye giremez. Provider routing tüm fallback adaylarını policy'ye göre kontrol eder. İnternet yokken sesli görüşme sürer; Agent için "Bu işlem çevrimdışı yapılamıyor" demek doğru davranıştır.

### 21.3 Kullanıcı verisinin geri çekilmesi

Kullanıcı bir geçmişi silmek istediğinde UI kayıt/özet geçmişi, Agent memory, local transcript, cache ve ilgili audio artifact arasındaki farkı açık tutar. Bazı audit kayıtları mevzuat veya güvenlik amacıyla sınırlı tutulabilir; silme sözünü teknik olarak gerçekleştiremiyorsak dürüstçe açıklanır. Eğitim Corpus hattına otomatik veri aktarımı yapılmaz; kullanıcı opt-in olsa bile [Corpus Governance](https://github.com/ImtheKaiwen/kaiwen-corpus/blob/3416d57ce0815af0cb8357c6727cd4ba889bd46d/docs/DATA_GOVERNANCE.md) lisans/izin ve dataset export sözleşmeleri geçerlidir.

## 22. Kaynak gösterimi, güvenilirlik ve kullanıcının bilgi ihtiyacı

Agent harici bilgi getirdiğinde cevap; bilginin kaynağı, alınma zamanı, doğrulama durumu ve varsa belirsizliği ayırır. "Güncel hava durumu" gibi dış sistem gerektiren isteğe cevap kaynak verilmeden sunuluyorsa UI bunu doğrulanmış gerçek zamanlı bilgi gibi etiketlemez. Tool sonucunun `success` olması, içeriğin doğru ve yeterli olduğu anlamına gelmez. Birden fazla kaynak çelişirse Agent'ın cevabı bunu belirtebilir; Live açıklayıcı kaynak/kanıt alanını saklamadan gösterir.

Kaynak verileri kısa tutulmalı; özel dosya içeriği, auth URL'leri veya query parametrelerinde token UI'da paylaşılmaz. Kullanıcı kaynağa tıklarsa seçilmiş güvenli URL, OS shell'in/izole tarayıcının allowlist doğrulamasından geçer; `javascript:` ve yerel dosya protokolleri otomatik açılmaz. Kaynak metnindeki talimatlar yine policy değildir. Ekran okuyucu uzun URL yerine anlamlı kaynak başlığını duyurur.

### 22.1 Sonuç doğruluğu ve sınırları

- `agent completed` ve `tool completed` farklı olaylardır.
- Yanıtın referansları varsa UI bunları modelin metninden değil, typed tool provenance alanından almayı tercih eder.
- `tool_result` yetkili dış API'dan geldi diye doğruluğu mutlak kabul edilmez; tarih ve kapsam belirtilir.
- Yan etkili işlem `verified_external_action=true` ancak receipt ve başarılı provider yanıtı temellendiriyorsa gösterilir.
- Araç kullanımı reddedildiyse normal sohbetten üretilen açıklama, araştırılmış dış bilgi olarak gösterilmez.

## 23. Bellek ve uzun konuşma bağlamı

Kaiwen Agent uzun dönem hafıza ve session summary bileşenlerine sahip olsa da Live'ın kullanıcı konuşmasını varsayılan olarak kalıcı Agent memory'e aktarması yanlıştır. Konuşmadan gelen Agent isteği **minimum gerekli özet veya son tur** ile sınırlandırılır. UI metin isteği yeterliyse tüm ham transcript geçmişini dış provider'a göndermeyiz. Uzun bağlam sağlanacaksa kullanıcıya hangi konuşmaların kullanımda olduğu gösterilebilir.

Agent `SessionMemoryManager`, `LongTermMemoryManager` ve context budget özellikleri host tarafından ayrıca yapılandırılmalıdır; import edilmesi aktif hâle gelmeleri demek değildir. Veriler kullanıcı/tenant kapsamına bağlıdır. Context summary, audit/approval kayıtlarının yerine geçmez. Önemli yan etkili görevin önceki onay parametreleri kısa bellekte tutulsa bile yeni action için tekrar doğrulama gerekir. Kullanıcı "bu konuşmayı hatırlama" istediğinde bellek politikasının kapsamı açıklanır ve izinli silme/retention mekanizması kullanılır.

### 23.1 Prompt bütçesi

CPU/GPU ve maliyet hedeflerine göre: system instructions, tool schemas, son kullanıcı komutu, gerekli konuşma özeti, yapılandırılmış tool çıktıları ve response rezervi ayrı ölçülür. Tool schema'ları text-only chat yolunda modele sunulmaz. Context window taşarsa Agent kontrollü hata veya compact/retry politikası uygular; rastgele transcript silinmesiyle eylemin hedefi değiştirilmez.

## 24. Farklı provider stratejileri ve model yetenekleri

Agent provider seçimi `ModelCapabilities`, `ProviderRegistry`, `ModelRouter` ve ürün `WorkspaceProfile` üzerinden yönetilebilir. Bunların önemli ayrımı: **teknik model kabiliyeti yetki değildir**. Bir model tool calling destekliyorsa kullanıcı hesaplarına erişim otomatik açılmaz. Yerel Ollama provider'ı varsa bilinen tool stratejisinin o model için uygunluğu ayrıca test edilir; "modelin kendisi kurulu" iddiası runtime probe olmadan çıkmaz.

| Provider modu | Olumlu yön | Maliyet / risk | V1 kararı |
|---|---|---|---|
| Mock/fake | Şemasal ve UI testi hızlı | Gerçek bilgi/araç yok | Zorunlu test düzlemi |
| Yerel text provider | Offline veri yerelliği | RAM/VRAM, kurulum, latency | Kullanıcı kurarsa opsiyonel |
| Onaylı bulut provider | Daha geniş model seçenekleri | Ağ, ücret, kişisel veri aktarımı | Açık opt-in olmadan kapalı |
| Retrieval-only adapter | Dar dış bilgi erişimi | Lisans, güncellik, prompt injection | Read-only slice sonrası |
| Durable workflow | Uzun ve çok adımlı görev | Persistence/recovery ve yetki maliyeti | V1 sonrası |

2 GB sınıfı VRAM, yalnız Speech'in çalışabileceği araştırma hedefidir; yanında bir LLM veya TTS'nin aynı GPU'ya yerleşeceği garanti değildir. Agent worker GPU rezervasyonunu Speech'le paylaşacaksa kaynak yöneticisi net politikaya sahip olmalıdır. Ses oynatma görevleri GPU belleği zorlayan yardımcı modelin arkasında bloke edilmez. Gerekirse Agent CPU'da/dış cihazda çalışabilir; kullanıcı local-only tercihine sadık kalınır.

## 25. Resource governance, latency ve backpressure

Her queue bir iş yükü sınıfı, sahiplik, kapasite ve reddetme davranışına sahiptir. Speech output PCM kuyruğu gerçek zamanlı playback gerektirir; Agent tool queue'su ise daha uzun beklemeyi kabul edebilir. Bu iki kuyruk tek global event loop/tek FIFO altında tutulursa uzun bir retrieval işlemi ses gecikmesini artırabilir.

| Queue | Tipik yük | Düşürme/retry politikası | Öncelik |
|---|---|---|---|
| Microphone PCM | Kısa ikili ses frame'leri | Bounded; kayıp teşhis edilir | En yüksek |
| Playback PCM | Üretilmiş ses frame'leri | Stale generation reddi; underrun ölçümü | En yüksek |
| Session control | Cancel, close, device change | Idempotent, güvenilir teslim | Yüksek |
| Agent approval | Kullanıcı kararı | Kaybolursa fail-closed | Yüksek |
| Agent request | Metinsel görev | Bounded queue, user-facing reject | Normal |
| Agent progress | Düşük öncelikli durum | Coalescing/sampling | Düşük |
| Telemetry | Aggregate metrikler | Sampling/drop, mahremiyet | Düşük |

**Ölçümler:** `agent_request_to_start_ms`, `agent_first_progress_ms`, `agent_total_ms`, `tool_wait_ms`, `approval_wait_ms`, `agent_queue_depth`, `agent_rejection_count`, `agent_provider_errors`, `speech_ttfa_ms`, `playback_underrun_count` ve `voice_result_first_pcm_ms`. Agent süresini Speech TTFA'ya karıştırmak performans regresyonunu saklar. Aynı donanım üzerinde Agent kapalı/açık iki profili karşılaştırılmadan "gecikmeye etkisi yok" iddiası yapılmaz.

### 25.1 Admission policy

UI çift tıklamasından gelen duplicate submit önce dedup edilir. Sıraya alınacak işi backend değerlendirir: Agent özelliği açık mı, gerekli provider hazır mı, owner quota dolu mu, tool seti izinli mi, session hâlâ aktif mi? Kaynak yetersizse açık hata döner. Sınırsız `asyncio.create_task` veya her yeni transcript chunk'ı için otomatik yeni Agent job'u üretme yasaktır.

### 25.2 Performans raporu

Benchmark raporu için ortam: OS, CPU, GPU/VRAM, Speech release ve codec, Agent SDK sürümü, Agent model/provider, ağ modu, cache cold/warm, audio cihazı, input uzunluğu, tool tipi, onay varlığı ve tekrar sayısı kaydedilir. Latency p50/p95/p99 ve zaman aşımı oranı birlikte değerlendirilir; tek başarılı ekran videosu performans ispatı değildir. 2 GB VRAM hedefi yalnız belirli cihaz profilinde ölçülmüşse o profille sınırlı ilan edilir.

## 26. Hata sınıfları, kullanıcı mesajı ve fallback matrisi

| Hata kodu (HEDEF) | Nedeni | Güvenli davranış | Kullanıcıya özet |
|---|---|---|---|
| `AGENT_DISABLED` | Kullanıcı özelliği kapatmış | İstek gönderme; ses devam | "Ajan özelliği kapalı." |
| `AGENT_PROVIDER_UNAVAILABLE` | Local/remote provider yok | Cloud'a gizli geçme | "Ajan şu anda kullanılamıyor." |
| `AGENT_INPUT_INVALID` | Boş/aşırı uzun metin | Reddet, düzeltme iste | "İsteği düzenleyin." |
| `AGENT_CAPABILITY_DISABLED` | İlgili araç/devam modu kapalı | Fail-closed | "Bu işlem etkin değil." |
| `AGENT_PERMISSION_DENIED` | Policy/owner reddi | Tool çalıştırma | "Bu işlem için izin yok." |
| `AGENT_APPROVAL_REQUIRED` | Onay kapısı yok | Eylem yapma | "İşlem onay bekliyor." |
| `AGENT_APPROVAL_DENIED` | Kullanıcı reddetti | Eylemi sonlandır | "İşlem yapılmadı." |
| `AGENT_APPROVAL_EXPIRED` | Onay zamanı geçti | Yeni onay almadan devam etme | "Onayın süresi doldu." |
| `AGENT_QUEUE_FULL` | İş kuyruğu dolu | Yeni işi reddet | "Şu an çok fazla işlem var." |
| `AGENT_TIMEOUT` | Provider/tool süre aşımı | Eylem türüne göre belirsizlik | "İşlem zaman aşımına uğradı." |
| `AGENT_ACTION_UNCERTAIN` | Dış etki teyitsiz | Otomatik retry yapma | "Sonuç doğrulanamadı." |
| `AGENT_PROTOCOL_INCOMPATIBLE` | SDK/IPC sürümü uyuşmaz | Feature kapat | "Ajan bileşeni güncelleme gerektiriyor." |
| `AGENT_OUTPUT_UNAVAILABLE` | Voice renderer yok | Metin fallback | "Yanıt metin olarak gösterildi." |
| `AGENT_SESSION_INVALID` | Session kapanmış | Eski yanıtı active UI'ya iletme | "Eski oturumdan yanıt alınamadı." |
| `AGENT_PROCESS_CRASHED` | Worker çöktü | Recovery/uncertain ayrımı | "Ajan yeniden başlatılıyor." |
| `AGENT_DATA_LOCALITY_DENIED` | Local-only ihlali | Bulut isteğini engelle | "Bu işlem çevrimdışı yapılamıyor." |
| `AGENT_TOOL_SCHEMA_INVALID` | Tool input uyuşmaz | İşlemi başlatma | "İşlem verileri geçersiz." |
| `AGENT_CANCEL_NOT_CONFIRMED` | Dış iptal teyitsiz | Başarı/iptal ilan etme | "İptal durumu doğrulanamadı." |

Kullanıcı hata mesajları mahrem tool argument'larını veya secret değerlerini dökmez. Diagnostik ekranı tersine çevrilebilir bir `correlation_id`, hata kategorisi ve kaynak bileşen verir. Hata nedeniyle Fast Path'in otomatik kapanması gerekmiyorsa kapatılmaz. Tool authorization hatasında "başka provider deneyeyim" fallback yapılmaz.

## 27. Arayüz tasarımı ve erişilebilirlik

Agent eklentisi, Kaiwen Live'ın minimalist ana konuşma deneyimini kalabalıklaştırmamalıdır. Kullanıcı default ekranda mikrofon ve durum bilgisini görür. Agent isteği açıkça etkinleştirildiğinde daha küçük bir ayrıntı paneli, görev geçmişi veya tool onayı görüntülenir. Kaiwen Design'ın gerçek `Button`, `Card`, `Modal`, `Tooltip`, `ToastProvider`, `Progress`, `ErrorState` gibi bileşenleri kullanılır; Agent onayı için kopya bir genel UI kütüphanesi kurulmaz.

### 27.1 Agent görev kartı

Bir görev kartında başlık, yetenek etiketi (`Metin yanıtı`, `Bilgi arama`, `Dosya eylemi`), durum, hangi istekten kaynaklandığı, gerekirse kaynaklar, iptal eylemi ve sonuç olur. Kart yalnız anlamlı durum geçişlerinde animasyon yapar; her token için layout değişimi yapılmaz. Kullanıcı kartı gizleyebilir; bu işlem job iptali değildir. Long-running task için açıkça "arka planda devam ediyor" metni yer alır. Yan etkili eylem tamamlanınca receipt/sonuç bağlantısı varsa gösterilir.

### 27.2 Onay modalı

Modaldaki en önemli bilgi "ne değişecek" sorusunun yanıtıdır. Sadece "Emin misin?" yazılması yeterli değil. Hedef dosya, alıcı, mesaj içeriği veya finansal tutar gibi etkili parametreler okunabilir gösterilir. Klavye tab sırası, focus trap/restore, Escape davranışı ve ekran okuyucu duyurusu test edilir. Escape/onay modalını kapatma, işlemi onaylamak değildir. Onay verilirse yalnız karşılık gelen `approval_id` ve checksum üzerinde karar oluşur. Oturum kapandığında pending approval varsayılan olarak geçersizleşir.

### 27.3 Sesli ve görsel durum

Ekran okuyucu için Agent progress spam yapılmaz; `aria-live=polite` kritik durumlarda kısa duyuru için kullanılır. Hata/approval için uygun rol kullanılır. Motion policy `prefers-reduced-motion`'ı aşamaz. Kullanıcıya Agent bekleme durumunu yalnız animasyon rengiyle bildirmek yasaktır. Kapalı mikrofon simgesi Agent'ın bilgisayara dış ağ erişimi olmadığını anlatmaz; gizlilik ayrı, görünür ayarla kontrol edilir.

### 27.4 Kaynak ve çıktı görünümü

Uzun Agent yanıtı tipografi ve paragraf sınırlarıyla okunur. Kaynak linkleri veri kaynağına göre ayrı değerlendirilir. Modelin ürettiği Markdown güvenli render edilir; HTML, script ve yerel komutlar varsayılan olarak yürütülmez. Sesli çıktı varsa kullanıcı `Sesli oku`/`Sustur` eylemiyle kontrol eder. Kullanıcının "sesli oku" düğmesine basması herhangi bir dış eylemi yeniden başlatmamalıdır.

## 28. IPC güvenliği, process sınırı ve secrets

Electron `contextIsolation: true`, dar preload API, tercihen sandbox ve güvenli CSP ile çalışır. Renderer doğrudan Python subprocess başlatmaz, keyfi URL fetch ile Agent sidecar'a erişmez, `window.require` veya Node.js modülleri üzerinden tool çalıştırmaz. Electron main, trusted session ve origin doğrulaması yapar. Sidecar mümkünse loopback veya named-pipe ve kısa ömürlü ephemeral secret ile korunur; localhost olmak tek başına yetki doğrulaması değildir.

### 28.1 IPC abuse senaryoları

- Kötü niyetli renderer script'i `tool.execute("delete")` mesajı gönderir: tipli semantic API ve backend policy reddeder.
- Başka local process sidecar portunu keşfeder: channel auth ve session token doğrulaması gerekir.
- `file://` veya `javascript:` URL tool sonucuyla gelir: UI'da otomatik açılmaz.
- Tool output gizli `api_key` anahtarı içerir: audit/log/telemetry'de redakte edilir.
- Renderer bozuk `sequence` ve eski `session_epoch` mesajı yollar: IPC doğrulayıcı reddeder.
- Agent SDK sürümü değişir, event schema alanı eksilir: feature negotiation kapatır, araç çalışmaz.
- Local STT adapter indirilen ses modelini gizlice farklı cloud sağlayıcıdan çağırır: local-only ve dependency audit başarısız sayılır.

### 28.2 Güvenli configuration

Yayın paketine API anahtarı, kişisel erişim token'ı, sabit loopback auth secret veya dosya sistemi yazma yetkisi gömülmez. Kullanıcı kurulu agent provider'ı seçebilir ancak her provider'ın veri yerelliği/ücret/izin etkisi açıkça raporlanır. Secrets OS korumalı depolamada veya backend provider boundary'sinde kalır. Debug modunda log seviyesini artırmak ham mikrofona erişme izni sağlamaz.

## 29. Dayanıklı job/approval'ın depolama politikası

Uzun görevler için in-memory job store restart sonrasında yeterli değildir. Kaiwen Agent'ın SQLite veya başka durable store adapter'ları gerçekten kurulur, schema/version migration yazılır ve owner-scoped okuma test edilir. Live renderer pending approval'ları localStorage içine yazarak kanonik durum tutmaz. Approval/intent kayıtları backend tarafında tutulur; UI yalnız sınırlı görünüm alır.

**Retention ve migration:** Raw transcript yerine görev durumu ve minimum audit saklanır. Veri minimizasyonu ile güvenlik ihtiyacı birlikte değerlendirilir. Eski release'den yeni release'e geçerken önce DB snapshot/backup, sonra transactional migration, sonra startup integrity check. Bozuk migration'da kullanıcı onay kayıtları kaybolursa Agent mutating capability fail-closed olur. Tek makinede çoklu process kullanılırsa SQLite transaction/lock ve ayrı process aynı kayda yazma yarışı test edilir.

### 29.1 Owner scope

Her durable kaydın tenant/user/session veya ilgili conversation ID'si kayıtlı olmalıdır. Tek kullanıcı modu bu alanları boş bırakarak "herkese açık" storage kurulması anlamına gelmez. Başka user/session'a ait job sonucuna yalnız trusted mapping ve uygun yetkiyle erişilir. Ses cihazının seçilmiş olması kullanıcı kimliği değildir.

## 30. Agent entegrasyonu için sözleşme sürümleme ve migration

Kaiwen Live, `kaiwen.live.session` IPC protokolünü, Agent SDK sürümünü, model/provider yeteneğini ve tool schema sürümlerini birbirinden ayrı yönetir. Yalnız `agent_sdk_version=0.7.0a1` görmek ürünün action/approval/voice desteklediğini kanıtlamaz. Ek olarak modelin yetenekleri, kurulu backend adapter, izinli tool registry ve health kontrolü gerekir.

### 30.1 Sürüm matrisi

| Bileşen | Kimlik | Değişiklik sınırı |
|---|---|---|
| Live IPC | `protocol_name` / `protocol_version` | Major değişiklikte eski client reddi veya adapter |
| Live Agent Bridge | `bridge_schema_version` | Request/result alanları ve durum mapping'i |
| Agent Python | `kaiwen-agent` pin | Runtime API/exception uyumu |
| Agent tools | `tool_name` ve version/checksum | Schema, onay ve idempotency |
| Agent workspace profile | Exact profile version | Yetki ve provider sınırı |
| Speech artifact | Release/codec/manifest | Hangi native output var? |
| TTS adapter | Engine/model/voice/PCM config | Ses uyumluluğu ve kalite |
| Device/backend | Windows audio API ve format | Playback latency ve interruption |

`capability=true` ancak producer/consumer sözleşmesi ve en az bir contract testini geçtiğinde yayınlanır. Bilinmeyen major IPC sürümüne güvenli reddetme uygulanır; yeni minor alanlar ileri uyumluluk politikası açıkça tanımlıysa görmezden gelinebilir. Yeni mandatory alan ekleme major migration gerektirebilir. Eski paketleri otomatik gerçek araç çalıştırmaya zorlayacak dönüşüm yasaktır.

### 30.2 Kaynak sözleşmeleri arasında farklar

Live'ın ses protokolünde `session_id`, `turn_id`, `generation_id`, `session_epoch` kullanılması Agent'ın kendi `AgentContext` tipleriyle aynı alan adlarını birebir eşitlemeyi gerektirmez. Adapter bu iki dünyanın mapping'ini açık yapar. Agent'ın `RealtimeSessionManager` modeli ile Live session state makinesi farklı ürün sorumlulukları taşır; aynı `status` ismini kullanmaları aynı durum geçişleri demek değildir. Tek bir kanonik "agent_completed" semantiği seçilir ve kaynak event'lerinden eşlenir.

### 30.3 API belgelerindeki işaretli açık kararlar

Speech/Forge/Integration belgelerinde daha önce fark edilen release manifest adları arasında uyumsuzluk bulunabilir. Agent bridge doğrudan model artifact şemasını yeniden tanımlamamalıdır; doğrulanmış Forge release ve Speech runtime capability'sini tüketir. `kaiwen.model.release` kanonik önerisinin diğer belgelerde tekleştirilmesi ayrı cross-repo migration işidir. Bu dosya yazıldığı için bu düzeltme kodda gerçekleşmiş sayılmaz.

## 31. Gerçekçi kullanıcı senaryoları ve sıralama

### Senaryo A — Normal sohbet, Agent kapalı

Kullanıcı mikrofonu etkinleştirir ve Türkçe doğal diyalog başlatır. Live doğrudan Speech runtime'ını kullanır. Agent için hiçbir process veya provider açılması zorunlu değildir. Mikrofon izinleri, codec, inference ve playback mevcut ses sözleşmesine göre işler. Agent'ın devre dışı olması UI'da bilinebilir ancak konuşmayı kesmez. Kabul testi fake Agent modülünü kasıtlı hata yaptırarak Speech'in çalışmaya devam ettiğini gösterir.

### Senaryo B — Açık metin bilgisi

Kullanıcı "Ajan'a sor" alanına "Bana HTTP cache'i açıkla" yazar. Backend input'u doğrular, trusted identity üretir, toolsuz `chat()` başlatır ve metin cevabını döndürür. Live, bunun internet araştırması değil model açıklaması olduğunu bilir. Seslenme butonu yalnız `tts_bridge` gerçekten hazırsa çalışır; değilse metin görünür. Oturum kapalıysa geçmiş request ID üzerinden terminal durum isteğe bağlı görev geçmişine taşınabilir.

### Senaryo C — Salt-okunur dosya araştırması

Kullanıcı yalnız izin verdiği çalışma alanındaki `README.md` dosyasını özetlemek ister. Live `action()` için tek bir trusted `workspace.read` tool'unu açar; Agent'ın WorkspaceFilesystem adapter'ı sandbox ve byte limit uygulayabilir. Dosya var değilse veya izin dışı konumdaysa tool reddeder. UI "Dosya okunamadı" der; başka klasörleri otomatik taramaz. Prompt injection içeren dosya tool setini değiştirmez. Erişim kaynağı ve doküman sürümü sonucu eşlik eder.

### Senaryo D — Not yazma ve onay

Kullanıcı "Proje notuna toplantı tarihini ekle" der. Agent intent doğrulaması ve uygun tool schema'dan sonra explicit approval ister. UI hedef dosyayı ve eklenecek metni gösterir. Kullanıcı onay vermezse dosyaya yazılmaz. Onay verdiğinde Agent'ın durable action intent ve audit yoluyla işlem yapılır; işlem sonucu receipt beklenir. Timeout olursa "Belirsiz" durumu ayrılır, ikinci yazma otomatik yapılmaz. Gerçek Windows dosya ve izin senaryosunda test edilir.

### Senaryo E — Sesli intent, STT hatası

Ayrı sesli Agent modu etkin. Kullanıcı "notu göster" der, STT "notu gönder" duyabilir. Sistem dosya gönderimi gibi daha yüksek riskli eyleme geçmeden kullanıcının doğrulamasını ister. Düşük güven ve belirsiz hedefte görev oluşturmaz. Bir başka kişinin sesi duyulsa bile kullanıcı hesabı adına mutating eylem otomatik onaylanmaz. Bu senaryo otomatik intent'in ilk sürüm için neden ön koşul olmadığını gösterir.

### Senaryo F — Agent sonucu kullanıcı konuşurken gelir

Agent bir çevrimdışı modelden cevap üretirken kullanıcı Fast Path'te yeni konuya başlamıştır. Agent sonuç event'i eski `turn_id` ile gelir. Live sonucu sessiz bildirimde ve görev kartında gösterir; yeni kullanıcı konuşmasının audio generation'ı arasına PCM sokmaz. Kullanıcı isterse sonucu dinletir. Bu anda Speech native streaming aktifse bile TTS ayrı generation ID üzerinden yürütülür. Session epoch değişmişse eski session output queue'ya girmez.

### Senaryo G — Dış eylem timeout ve uygulama çökmesi

İzinli bir yan etkili tool başlar; dış sağlayıcı yanıt vermeden Live kapanır. Restart sonrası store `executing` işlem tespit eder ve güvenilir receipt yoksa `uncertain` olarak bloke eder. UI kullanıcıya kaynak servis kontrolü olmadan "yapılmadı" demez ve otomatik tekrar yapmaz. Durable approval olmadan eylem önceden başlatılmışsa bu bir güvenlik ihlalidir; testin başarısız olması release'i engeller.

### Senaryo H — Local-only seçilmiş, Agent internet gerektiriyor

Bir bilgi arama isteği dış ağ gerektirir. Provider router `local_only` politikasını kontrol eder, bu araç için `AGENT_DATA_LOCALITY_DENIED` döner; gizli API anahtarı veya otomatik Google/web call yoktur. Kullanıcıya işlemin neden yapılamadığı açıklanır, fakat temel sesli sohbet devam eder. İnternet açılınca aynı isteğin otomatik başlatılması yerine kullanıcıdan yeni eylem veya açık bir takip mekanizması gerekir.

## 32. Test stratejisi: kanıt basamakları

Üç ayrı kanıt düzeyi vardır:

1. **Contract/unit:** Fake provider ve deterministic fixture; Python/TS schema, event mapping, izin, iptal, dedup. Gerçek ses/dış hizmet kullanılmaz.
2. **Integration:** Gerçek Agent runtime, yalnız izinli ve izole araç, local IPC, SQLite store, Electron UI ve Speech batch adapter. Dış ağ gerekmez; gerçek Windows audio sürücüsü bağımlılığı test özelinde seçilir.
3. **System/hardware:** Gerçek mikrofon, gerçek Speech modeli, opsiyonel TTS, gerçek onay UX, GPU bütçesi, speaker loop, uzun oturum. Bu düzeyde ölçülmemiş özellik "validated" sayılmaz.

Temel kalite kapıları: request JSON schema, Python/TypeScript typecheck, linter, test runner, paketleme, Windows smoke, offline profile, approval ve crash safety. Agent'ın kendi CI'sı geçmiş olsa bile Live'ın OS cihazı ve IPC yetki testleri ayrıca gereklidir. Fake tool sonucunu gerçek e-posta gönderimi veya web erişimi gibi göstermeyi engelleyen görünür mod etiketi test edilir.

### 32.1 Test matrisi — 50 kritik durum

| ID | Test | Kabul koşulu |
|---|---|---|
| AGT-001 | Agent tamamen kapalı | Speech batch konuşması etkilenmez |
| AGT-002 | Agent SDK import hatası | UI capability false, crash yok |
| AGT-003 | Fake provider toolsuz chat | Metin sonucu ve doğru `fake` etiketi |
| AGT-004 | Boş input | Şema hatası, run açılmaz |
| AGT-005 | Uzun input | Bounded rejection, bellek taşması yok |
| AGT-006 | Aynı `request_id` iki submit | Tek iş, aynı owner sonucu |
| AGT-007 | Aynı ID başka user | Owner izolasyonu, conflict/reject |
| AGT-008 | Chat modunda tool çağırma isteği | Tool registry görünmez |
| AGT-009 | Action modunda izinsiz tool | Reddedilir; tool çalışmaz |
| AGT-010 | Read-only tool izinli root | Belirlenmiş dosya okuma başarılı |
| AGT-011 | `../` path traversal | Sandboxed erişim reddi |
| AGT-012 | Symlink ile root dışına kaçış | Erişim reddi |
| AGT-013 | MCP discovery'de yeni tool | Açık kayıt/izin olmadan çalışmaz |
| AGT-014 | Malicious tool output | Yetki ve system prompt değişmez |
| AGT-015 | Approval yokken yazma | Fail-closed; dosya değişmez |
| AGT-016 | Approval kullanıcı tarafından reddedildi | Tool çağrılmaz |
| AGT-017 | Approval timeout | İşlem yetkilendirilmez |
| AGT-018 | Başka run'ın approval ID'si | Yeniden kullanılamaz |
| AGT-019 | Onaydan sonra argument değişimi | Checksum mismatch ve yeni onay |
| AGT-020 | Mutating action çift submit | İdempotency ile tek etki |
| AGT-021 | Dış API timeout | Sonuç `uncertain`, otomatik retry yok |
| AGT-022 | Process crash sırasında write | Restart sonrası reconciliation |
| AGT-023 | Restart sonrası pending approval | Doğru owner doğrulanmadan açılmaz |
| AGT-024 | Session kapatılırken read-only run | Açık lifecycle/policy uyarınca cleanup |
| AGT-025 | Session kapanırken durable job | Yan etki durumu doğru korunur |
| AGT-026 | `stop_playback` çağrısı | Agent job beklenmedik şekilde iptal edilmez |
| AGT-027 | `cancel_generation` çağrısı | Agent request yanılgıyla silinmez |
| AGT-028 | `cancel_agent_request` | Tek request scope iptali; açık ack |
| AGT-029 | `cancel_agent_job` | Dış etki gerçekleşmişse belirsizlik korunur |
| AGT-030 | Eski session epoch sonucu | Aktif ses kuyruğuna girmez |
| AGT-031 | Eski turn sonucu yeni konuda | Sessiz görev kartı, otomatik ses yok |
| AGT-032 | Out-of-order Agent progress | Terminal state yeniden açılmaz |
| AGT-033 | Bilinmeyen event schema | Capability düşer, yanlış success yok |
| AGT-034 | Queue taşması | Bounded reject, PCM etkilenmez |
| AGT-035 | Provider yavaş/çöktü | İstenen timeout/hata kodu |
| AGT-036 | Local-only network yok | Cloud fallback kesinlikle yok |
| AGT-037 | Local-only ama cloud provider configured | İstek başlamadan reddedilir |
| AGT-038 | Secret içeren tool output | Log/telemetry redaksiyonu |
| AGT-039 | Renderer doğrudan raw tool IPC | Allowlist/backend reddi |
| AGT-040 | Başka local process IPC'ye bağlanır | Channel auth zorunlu |
| AGT-041 | Cihaz değişimi sırasında Agent | Job korunur, audio callback block yok |
| AGT-042 | TTS adapter kurulu değil | Metin fallback, native voice iddiası yok |
| AGT-043 | TTS sonuç PCM üretimi | Sample format, generation ve playback test |
| AGT-044 | TTS çalarken barge-in | Stale PCM yeniden duyulmaz |
| AGT-045 | TTS output echo input'a girer | Yeni otomatik Agent action açılmaz |
| AGT-046 | Türkçe ASR kritik komutu yanlış tanır | Açık parametre onayı, action otomatik yok |
| AGT-047 | Web kaynağı result URL tehlikeli | Link açılması reddedilir |
| AGT-048 | Agent geçmişi/izin silme | Retention ve izinli cleanup çalışır |
| AGT-049 | Aynı GPU'da Speech + Agent/TTS | Peak VRAM/TTFA benchmark raporu |
| AGT-050 | Windows paket/upgrade migration | Onay ve action intent veri bütünlüğü |

Test ID'leri benzersiz ve sürüm üzerinden izlenir. Her test için fixture, çalıştırma komutu, beklenen çıktı, actual result ve fail condition CI raporunda tutulur. Test tablosu bir **plan**dır; bu dosyanın oluşturulması testlerin çalıştırıldığı anlamına gelmez.

## 33. Uygulama aşamaları: A0–A12

| Faz | En küçük teslim | Ön koşul | Kabul kapısı |
|---|---|---|---|
| **A0** | Gerçek repo/dependency/API keşfi | Başlangıç kod ağacı | SDK version ve mevcut/olmayan ayrımı |
| **A1** | `AgentBridge` typed interface + fixtures | Live IPC kontratı | Typecheck, schema tests |
| **A2** | Fake provider + bounded queue | A1 | AGT-001–008 |
| **A3** | Gerçek `AgentRuntime.chat` text-only | Agent paket pin'i | Offline integration, timeout |
| **A4** | Trusted identity ve policy mapping | A3 | Owner isolation, deny-by-default |
| **A5** | Bir salt-okunur allowlisted tool | A4 | Path sandbox, injection tests |
| **A6** | Approval UX + Agent gate | A5 | Pending/deny/expired cases |
| **A7** | Durable idempotent mutation | A6 | Crash, receipt ve uncertain tests |
| **A8** | Job manager ve task lifecycle | A7 (veya ayrı read-only job) | Restart/status/cancel |
| **A9** | İsteğe bağlı ASR intent yolu | A3 | STT yanlış tanıma ve manual confirmation |
| **A10** | Text result + source provenance polish | A3 | UX/accessibility/escaping |
| **A11** | Opsiyonel yerel TTS veya Speech conditioning | A10 + upstream gerçek model API | PCM, latency, mode labeling |
| **A12** | Full regression/hardware/packaging | Kapsama giren önceki fazlar | Release gate, rollback, metrics |

Bu sıra üst seviye yol haritasıdır; uygulama gerektikçe A10 text UI işi A6'dan önce bitirilebilir. Ancak **A7 yan etkili tool**, A6 onay ve dayanıklı action intent olmadan açılmaz; A11 voice output yeteneği, gerçek upstream konuşma üretim API'si olmadan "tamamlandı" denemez. A8 job manager'ın kendi persistence kapısını açmalıdır. `A9` sesli intent, MVP'nin ön koşulu değildir.

### 33.1 İlk PR sınırı (gerçekçi)

İlk PR: fake provider'a text input gönderen, gerçek tiplerle kurulu, izin gerektirmeyen bir `AgentBridge` adapter iskeleti, kontrat fixture'ları ve bir UI kartı. İkinci PR: gerçek `AgentRuntime.chat()` ve güvenilir local identity. Üçüncü PR: read-only tool allowlist. Daha sonraki PR'lar approval, mutating tools, jobs ve voice result. Bir PR'a hem native streaming codec değişikliği hem Agent approval sistemi hem Electron installer sıkıştırılmaz. Ayrıca bu projede yalnız dokümantasyon isteniyorsa PR veya GitHub push yapılmaz.

## 34. Uygulamaya hazırlık ve kontrol listesi

- [ ] Live repo ağacı ve gerçek bağımlılıklar doğrulandı; docs-only durumuyla kod ayrıldı.
- [ ] Speech Python import kökü ve inference kabiliyetleri gerçekten doğrulandı.
- [ ] Kaiwen Agent sürümü pinlendi ve `AgentRuntime` API contract testi geçti.
- [ ] Tool chat modu ile action modu ayrı; chat araçsız çalışıyor.
- [ ] Renderer ham tool komutu göndermiyor; sadece güvenli semantic IPC mevcut.
- [ ] Trusted `RuntimeIdentity`, session/turn/request/run eşleştirmesi test edildi.
- [ ] Local-only modda hiçbir remote provider'a gizli fallback yok.
- [ ] Tüm tool'lar server allowlist, schema, policy, onay ve sahiplik kontrolünde.
- [ ] Mutating tool ancak durable action intent/idempotency/approval doğrulanınca açılıyor.
- [ ] İptal semantiği: playback, Speech generation, Agent request, Agent job ayrı.
- [ ] `uncertain` sonuçları otomatik tekrar edilmiyor; kullanıcıya açıkça gösteriliyor.
- [ ] Ham ses, transcript, gizli anahtar ve özel argümanlar log'a dökülmüyor.
- [ ] Agent yanıtı metin olarak güvenli gösteriliyor; seslendirme `tts_bridge` veya `native_conditioned` olarak doğru etiketleniyor.
- [ ] TTS için Türkçe kalite, codec/PCM formatı, eski generation ve echo testleri var.
- [ ] Event, queue ve performans sınırları Speech audio callback'ini bloke etmiyor.
- [ ] 50 negatif/pozitif test planından uygulanan fazın kapıları CI'da geçiyor.
- [ ] Windows installer ve offline recovery, pinlenmiş SDK ile gerçekten çalışıyor.
- [ ] User-facing bilgiler gerçek capability/approval/job durumuna dayanıyor.

## 35. Codex teslim şablonu

Codex bir Agent entegrasyonu görevi bitirdiğinde aşağıdaki raporu verir. Tamamlanan iş ile dokümanda yazan hedef birbirine karıştırılmaz:

```text
GÖREV: <kısa ve sınırlandırılmış başlık>
KAPSAM: <Agent adapter / IPC / UI / TTS / test>
BAŞLANGIÇ: <branch, commit, tool ve paket sürümleri>
GERÇEK DURUM: <mevcut kod, eksik özellik, doğrulanan API>
YAPILAN DEĞİŞİKLİKLER: <tam dosya yolları>
SÖZLEŞMELER: <schema version, producer/consumer, migration>
GÜVENLİK: <identity, izin, onay, data locality, secret handling>
TESTLER: <komut, gerçek çıktı, geçen/kalan ID'ler>
DONANIM KANITI: <varsa GPU/CPU, OS, audio cihazı, ölçümler>
FAKE/GERÇEK AYRIMI: <hangi yol gerçekten çalıştı?>
GERİ ALMA: <migration, paket ve kullanıcı verisi koruma adımı>
AÇIK RİSKLER: <çözülmemiş blocker ve yeni kararlar>
SONRAKİ EN KÜÇÜK ADIM: <tek PR'ın somut kabul kriteri>
```

"Testler geçti" cümlesi çalıştırılmamış testler için yazılmaz. GitHub'da değişiklik veya yayınlama yapılmışsa commit/PR/release kanıtı verilir; kullanıcı istemediyse push yapılmaz. Başarısız negatif test saklanmaz. Performans raporu CPU/GPU ve cold/warm koşulunu içerir.

## 36. Açık tasarım kararları ve risk listesi

| ID | Karar | Alternatifler | Karar ön koşulu |
|---|---|---|---|
| AI-01 | Agent worker process düzeni | Aynı Python sidecar / ayrı process | CPU/VRAM ve crash izolasyonu benchmark |
| AI-02 | Live ↔ Agent event transport | IPC async event / local stream | Güvenlik ve burst testleri |
| AI-03 | Agent identity store | Tek kullanıcı local ID / kapsamlı account | Ürün yetkilendirme politikası |
| AI-04 | Read-only araç seti | Dosya okuma / kapalı / onaylı external API | Gerekli use-case ve risk |
| AI-05 | Voice output yolu | Text only / local TTS / learned conditioning | Gerçek upstream ses kalitesi |
| AI-06 | ASR intent sağlayıcısı | Yerel STT / açık metin girişi | Donanım ve yanlış tanıma oranı |
| AI-07 | İzin saklama | Session-only / explicit persisted grant | Mahremiyet ve least privilege |
| AI-08 | Uzun görev retention | Ephemeral / durable local DB | Gerçek kullanıcı ihtiyacı |
| AI-09 | Online provider | Kapalı / açık opt-in cloud | Hukuk, maliyet ve local-only ayrımı |
| AI-10 | Sesli yanıt play policy | Manuel dinletme / seçili otomatik | Echo, barge-in ve UX testleri |
| AI-11 | Auto tool routing | Sadece UI / ASR intent / model token | Türkçe veri, ölçülen precision/recall |
| AI-12 | Devam eden Agent işi ve session close | İptal / izinli arka plan | Kullanıcı ayarı ve crash recovery |

**En kritik riskler:** Speech-native modelde text conditioning bulunmaması, STT'nin etkili komutu yanlış tanıması, tool prompt injection, onay verilen parametrenin sonradan değişmesi, timeout sonrası çift yan etki, eski PCM'nin yeniden çalınması ve Agent/LLM/TTS nedeniyle 2 GB VRAM hedefinin aşılması. Bu riskler tek sloganla giderilemez; her biri ayrı karşılaştırma ve kabul testine bağlanmıştır.

## 37. Kapsam dışı konular

Bu sürüm için otomatik telefon araması, çağrı merkezi, SMS/e-posta gönderim otomasyonu, sosyal medya gönderisi, sürekli mikrofondan görev toplama, kullanıcı fark etmeden amaç takip sistemi, yönetici haklarıyla sınırsız shell, arbitrary code execution, kendi kendine yeni araç yükleme, distribüe multi-agent mesh, çok kullanıcılı SaaS ve cloud-hosted sürekli ses oturumu kapsam dışındadır. Kaiwen Agent'ın ayrı runtime'ında bu konulara yakın modüller bulunması Live'ın bunları desteklediği anlamına gelmez.

V1'in teknik başarısı daha dar ve anlamlıdır: **normal Türkçe konuşma yolunu kesmeden, kullanıcı tarafından açıkça başlatılmış bir Agent isteğini güvenilir kimlik, sınırlı yetki, doğru sonuç ve gözlenebilir hata yönetimiyle tamamlamak.** Sesli Agent cevabı V1'in temeline konulursa modelin henüz sağlamadığı text-conditioning çözümünü gizlemek zorunda kalırız. Bu araştırma açık problem olarak korunmalıdır.

## 38. Kaynaklar ve teknik okuma sırası

Aşağıdaki belge ve kod kaynakları uygulama öncesi okunur. Yerel bağlantılar bu çalışma alanındaki **gerçek** dosyalara yönelir. GitHub bağlantıları ayrı repository kaynaklarıdır:

1. [Kaiwen Live README](../README.md) — ürün sınırı, gerçek/fake modlar ve geliştirme planı.
2. [Kaiwen Live AGENTS](../AGENTS.md) — Codex kuralları, süreç ve test teslim standardı.
3. [Live Architecture](ARCHITECTURE.md) — sidecar IPC, PCM, session epoch ve interruption.
4. [Live Design and UX](DESIGN_AND_UX.md) — durum kartları, onay, mikrofon ve seslendirme.
5. [Workspace Integration](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/INTEGRATION.md) — ortak JSON event envelope ve cross-repo sınırı.
6. [Workspace Engineering Standards](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/ENGINEERING_STANDARDS.md) — sürüm, test, dokümantasyon, güvenlik.
7. [Workspace Roadmap](https://github.com/ImtheKaiwen/kaiwen-ai/blob/a2476114c4da048090aeb23a2b03a2ec930b113a/docs/ROADMAP.md) — özellikleri gereksiz genişletmeyen gelişim sırası.
8. [Speech API](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/API.md) — bugün mevcut `kaiwen_voice` ile hedef Speech SDK arasındaki sınır.
9. [Speech Streaming](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/STREAMING.md) — playback stop, cancellation, turn/generation kimliği.
10. [Speech Performance](https://github.com/ImtheKaiwen/kaiwen-speech/blob/2dd8ae4ff4970fec13d761afbb5587b887957547/docs/PERFORMANCE.md) — TTFA, RTF, VRAM ve benchmark yöntemi.
11. [Forge Model Registry](https://github.com/ImtheKaiwen/kaiwen-forge/blob/8bf2af3b925bc1478328b4a26fcba36af74480fb/docs/MODEL_REGISTRY.md) — model release/manifest doğrulaması.
12. [Corpus Data Governance](https://github.com/ImtheKaiwen/kaiwen-corpus/blob/3416d57ce0815af0cb8357c6727cd4ba889bd46d/docs/DATA_GOVERNANCE.md) — kişisel veri, ses kaydı ve izin.
13. [Kaiwen Agent repository](https://github.com/ImtheKaiwen/kaiwen-agent) — SDK'nın gerçek kaynak kodu.
14. [Agent consumer brief](https://github.com/ImtheKaiwen/kaiwen-agent/blob/main/docs/consumer-agent-brief.md) — ürün adapter'ının güven sınırları.
15. [Agent unified runtime](https://github.com/ImtheKaiwen/kaiwen-agent/blob/main/docs/unified-runtime.md) — chat/action/workflow ve bileşen olgunluğu.
16. [Agent realtime core](https://github.com/ImtheKaiwen/kaiwen-agent/blob/main/docs/realtime.md) — provider-neutral realtime lifecycle; Speech native streaming'i değildir.
17. [Agent ecosystem integrations](https://github.com/ImtheKaiwen/kaiwen-agent/blob/main/docs/ecosystem-integrations.md) — workspace filesystem ve MCP kayıtları.
18. [Agent production controls](https://github.com/ImtheKaiwen/kaiwen-agent/blob/main/docs/production-controls.md) — backpressure, audit, secrets ve owner scope.
19. [Agent SDK Runtime](https://github.com/ImtheKaiwen/kaiwen-agent/blob/main/backend/src/kaiwen_agent/runtime/agent_runtime.py) — `chat`, `action`, `run` gerçek fonksiyon imzaları.
20. [Agent SpeechPipeline](https://github.com/ImtheKaiwen/kaiwen-agent/blob/main/backend/src/kaiwen_agent/speech/pipeline.py) — açık STT→text→TTS, native ses değil.

**Son karar:** Live, Speech ve Agent'ın kesişimi en küçük yetkili adapter'da tutulur. Agent araçlar ve dış eylemler için; Speech konuşma modeli için; Live ses donanımı, güvenilir UI ve kullanıcı kontrolü için tek sorumludur. Bu ayrım korunursa daha sonra native audio-control token'ları ve gerçek time-to-first-audio optimizasyonları eklemek mümkün olur, ancak bunların varlığı yalnız belgelerle değil, çalışan kod ve deney raporuyla kanıtlanır.
