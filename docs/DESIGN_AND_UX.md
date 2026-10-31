# Kaiwen Live — Design & UX: Türkçe Speech-Native Masaüstü Deneyimi

> **Belge türü:** Ürün deneyimi, UI mimarisi, erişilebilirlik, etkileşim ve doğrulama sözleşmesi.  
> **Repository:** [`ImtheKaiwen/kaiwen-live`](https://github.com/ImtheKaiwen/kaiwen-live)  
> **Hedef dosya:** `kaiwen-live/docs/DESIGN_AND_UX.md`  
> **Durum:** **HEDEF / HENÜZ UYGULANMADI.** GitHub `kaiwen-live` reposunda 30 Ekim 2026 itibarıyla yalnız başlangıç README'si doğrulanmıştır. Bu dosya kodun, tasarımın veya gerçek sesli demoların hazır olduğunu iddia etmez.  
> **Kapsam:** Windows masaüstü, tek yerel kullanıcı, Türkçe sesli görüşme, local-first. İlk dikey dilim gerçek cihazda çalışan turn-based ses, sonra native streaming.  
> **Sahiplik:** Live kullanıcı deneyimine ve ses aygıtları arayüzüne sahiptir; Speech model/codec, Forge model yayını, Design ortak UI, Agent opsiyonel araç kullanımından sorumludur.  
> **Teknik referanslar:** [Live README](../README.md) · [Live AGENTS](../AGENTS.md) · [Live Architecture](ARCHITECTURE.md) · [Workspace Integration](../../docs/INTEGRATION.md) · [Speech API](../../kaiwen-speech/docs/API.md) · [Speech Streaming](../../kaiwen-speech/docs/STREAMING.md) · [Forge Registry](../../kaiwen-forge/docs/MODEL_REGISTRY.md) · [Kaiwen Design](https://github.com/ImtheKaiwen/kaiwen-design).

---

## 1. Bu belgenin görevi ve gerçeklik sınırı

Bu belge, Kaiwen Live'ın **kullanıcının gördüğü ve kontrol edebildiği deneyimini** tanımlar. `[ARCHITECTURE.md](ARCHITECTURE.md)` süreçler, PCM akışı, IPC, oturum state machine'i ve audio callback sahipliğinden söz eder; buradaki belge ise aynı olayların ekranda nasıl temsil edileceğini, hangi eylemin ne zaman açılacağını, hatanın nasıl anlatılacağını ve davranışın nasıl test edileceğini belirtir. Burada tarif edilen kontroller tamamlanmış React bileşenleri değildir. Dolayısıyla bir AI kodlama ajanı bu taslağı uygulamaya dönüştürmeden **"hazır arayüz"** sonucu çıkaramaz.

İki ayrı tasarım seviyesi vardır: **görsel niyet** ve **ürün doğruluğu**. Görsel niyet sakin, minimal, kararlı, siyah/beyaz/gri ağırlıklı, güçlü tipografili ve ölçülü mikro animasyonludur. Ürün doğruluğu ise sesin gerçekte kaydedildiğini, modelin gerçekten hazır olduğunu, hoparlörden gerçekten ses çıktığını, iptalin gerçekten gerçekleştiğini ve kullanıcı izninin gerçekten verildiğini kanıtlayan olaylarla bağlıdır. Biri diğerinin yerini tutamaz. Kusursuz animasyonlu fakat modeli hiç çalıştırmayan ekran, çalışır sesli asistan değildir.

### 1.1 Status sözlüğü

| Etiket | Kullanılması gereken kanıt | Kullanıcıya görünen anlam |
|---|---|---|
| `MEVCUT — DESIGN` | Kaiwen Design'ın GitHub kodundaki paket/bileşen varlığı | İthal edilebilir ortak UI yapı taşları |
| `MEVCUT — SPEECH` | Kaiwen Speech'in doğrulanmış Python fonksiyonları | Bir integration hedefi; çalışan Live anlamına gelmez |
| `HEDEF — LIVE` | Bu belge ve [Architecture](ARCHITECTURE.md) şartnamesi | Geliştirilmesi gereken ürün davranışı |
| `DENEYSEL` | Gerçek cihaz benchmark ve kontrollü test gerektiren özellik | İleri seviye, garanti verilmemiş çalışma |
| `DESTEKLENMİYOR` | Capability manifestinde `false` veya gerçek implementasyon yok | Erişilemez kontrol ve açık neden |

**Kural:** `native_streaming` yalnızca gerçek incremental codec/model üretimi, event doğrulaması ve audio testleri geçildiğinde kullanıcıya açık çalışma modu yapılır. Bitmiş WAV'ın küçük parçalara bölünmesi, native streaming ile aynı şey değildir.

### 1.2 Ürün vaadi ve kabul edilebilir kalite

Kullanıcı uygulamayı açtığında en az bilişsel yükle iki sorunun cevabını görmelidir: **"Konuşabilir miyim?"** ve **"Şu an sesimle ne oluyor?"**. Model destekliyorsa Türkçe konuşma turu başlatılır; desteklemiyorsa kapalı kontrol yerine veya yanında anlaşılır bir çözüm sunulur. Pencere kapandığında kamera/mikrofon izinsiz açık kalmaz. Yanıt kesildiğinde eski ses geri dönmez.

UX başarısı kullanıcıyı ekranda tutmakla değil, işini **tek bakış, tek giriş, tek geri bildirim** ile tamamlayabilmekle ölçülür. Günlük kullanımda görünür metrik, terminal, JSON veya ses mühendisliği terimleri dayatılmaz. Gelişmiş teşhis bilgilerinin tümü isteğe bağlı **Diagnostics** ekranında bulunabilir.

## 2. Ürün ilkeleri — öncelik sırası

1. **Dürüst durum bildirimi:** Bir düğmeye tıklamak, işlemin gerçekleştiği anlamına gelmez. Durum backend'in doğruladığı olayla değişir.
2. **Ses öncelikli:** Ana ekranın merkezinde büyük bir sohbet metni editörü, model marketplace veya dataset tabloları yoktur. Kullanıcının görevi konuşmaktır.
3. **Az kontrol, açık kontrol:** Birincil eylem konuşmaya başlamak/bitirmektir. Durdur/iptal ayırt edilmesi gereken durumlarda ayrı gösterilir.
4. **Local-first:** Varsayılan olarak mikrofon sesi uzak sunucuya veya diske gönderilmez; tüm uzak eylemler açık onay ve görünür etiket ister.
5. **Kesintiye dayanıklılık:** Cihaz çıkarılırsa, model çökerse veya izin reddedilirse sessizce sonsuz loading gösterilmez.
6. **Ölçülü hareket:** Mikro etkileşim durumu açıklamak için vardır; oyuncak gibi sürekli oynayan ekran tasarlanmaz.
7. **Klavye ve erişilebilirlik:** Mikrofon kontrolü klavye, ekran okuyucu ve reduced-motion ile kullanılabilir.
8. **Gerçek performans:** Renderer animasyonu audio callback'i bloke etmez; pahalı waveform işlemi ekran thread'inde yapılmaz.
9. **Tasarım sistemi tek kaynak:** Ortak Button, Modal, Switch gibi bileşenler `@imthekaiwen/ui-web` içinden kullanılır.
10. **İleri özellikleri öteleme:** V1 için servis yöneticisi, kalabalık plugin galerisi, zorunlu hesap açma ve agent marketplace yoktur.
11. **Güvenli varsayılan:** Otomatik kayıt, otomatik cihaz dinleme veya gizli arka plan Agent talimatı bulunmaz.
12. **Sade ama onarılabilir:** Hata ekranları teknik bir kimlik ve basit bir öneri taşıyabilir; kullanıcı yalnız "Bir şeyler ters gitti" ile bırakılmaz.

## 3. Hedef kullanıcı, kullanım bağlamı ve ana senaryolar

**Birincil persona:** Windows dizüstü bilgisayarında çalışan, Türkçe konuşmak isteyen, yerel modeli ve GPU'su sınırlı tek kullanıcı. Sistem özelliklerini bilen ama her konuşma turunda terminal açmak istemeyen araştırmacı/geliştirici. Bu persona ürünün tek makinede deneysel kullanılabilirliğini hedefler; bütün kullanıcıların teknik bilgi sahibi olduğu varsayılmaz.

**Günlük ana akış:** Uygulamayı aç → model hazır mı gör → izin gerekiyorsa ver → mikrofona bas → konuş → konuşma turunu bitir → yanıtı dinle → gerektiğinde kes veya yeni tur başlat → çık. Bekleme sırasında kullanıcı hangi işin sürdüğünü bilir.

**İkincil akışlar:** Mikrofon/hoparlör değiştirme; ilk model paketini yerel dosyadan ekleme; bozuk modeli geri alma; cihazı test etme; hata kodunu kopyalama; görünüm/motion değiştirme. Agent özelliği gelecekte isteğe bağlı ve ayrı yetki yüzeyi olacaktır.

**Kapsam dışı:** Telefon araması, telefon santrali, sosyal paylaşım, paylaşılan konuşma bulutu, otomatik metin dökümü arşivi, çok kullanıcı hesabı, çok oda, sürekli dinleyen wake word, gerçek zamanlı toplantı kaydı, kişisel ses klonlama. Kapsam dışı bir seçenek gizlice ayarlara yerleştirilmez.

### 3.1 Kullanıcı yolculukları ve görev başarı koşulları

| Yolculuk | Başlangıç koşulu | Başarı | Hata/geri dönüş |
|---|---|---|---|
| İlk açılış | Model bulunmayabilir | Uygun durum ve ilk sonraki adım belirir | Offline kullanıcıya geçersiz download butonu gösterilmez |
| Cihaz izni | Mikrofon izni bilinmiyor | OS izni sonrası gerçek capture olayı görülür | Reddedilirse kullanıcı ayar yoluna yönlendirilir |
| Konuşmaya başla | Model ve cihaz hazır | `listening` backend onayıyla başlar | Mikrofon açılamazsa mikrofon açık simgesi yakılmaz |
| Yanıt dinle | Input turu sonlandırıldı | Modelden gelen gerçek PCM çalınır | EOS boşsa "Yanıt üretilmedi" denir |
| Konuşmayı kes | Çıkış sesi oynuyor | Mevcut ses durur; eski generation çalmaz | Backend yanıtı geç gelirse stale veri reddedilir |
| Model değiştir | Aktif session var | Güvenli geçiş için oturum kapatılıp yeni release doğrulanır | İndirme/uyumluluk hatasında eski release korunur |
| GPU bellek hatası | Runtime başarısız | Kısıt bildirimi ve destekleniyorsa daha hafif model seçeneği | Otomatik "başarılı" etiketi yok |
| Uygulamadan çık | Kayıt sürüyor | Mikrofon bırakılır, sidecar kapatılır | Kapanış asılı kalırsa bounded timeout ve açıklama |

## 4. Bilgi mimarisi ve gezinme

**V1 görünür alanlar:** `Konuşma`, `Modeller`, `Ayarlar`; `Tanılama` ayarların altından erişilebilir. Sol sidebar ürün kullanımı için gerekli değilse dar ve isteğe bağlı; uygulamanın odağı ses oturumudur. Pencere ilk açıldığında karmaşık dashboard veya analytics duvarı bulunmaz.

```text
Kaiwen Live
├── Konuşma                     # ana ekran, tek aktif oturum
│   ├── Durum / model hazır mı?
│   ├── Ses durumu ve güvenilir görsel gösterge
│   ├── Birincil mikrofon eylemi
│   ├── Yanıtı durdur / tekrar dene / yeni tur
│   └── İsteğe bağlı son tur geçmişi (yalnız runtime metadata)
├── Modeller                     # yüklü ve uyumlu release'ler
│   ├── Aktif model, boyut, codec, doğrulama
│   ├── Yerel release ekleme
│   └── Geçiş, uyumluluk ve rollback
└── Ayarlar
    ├── Ses: giriş, çıkış, test, örnekleme
    ├── Görünüm: tema, motion, yoğunluk
    ├── Gizlilik: saklama, log, izinler
    ├── Tanılama: ölçümler, olaylar, hata kodu
    └── Hakkında: uygulama ve protokol sürümleri
```

Bu bilgi mimarisi kullanıcı testinde değişebilir; kararlaştırılmamış hiçbir metin veya kategori API şeması yerine geçmez. İlk sürümde büyük bir "Geçmiş" bölümü açılmamasının nedeni bilinçlidir: speech-native modelin otomatik doğru transkript ürettiği veya kullanıcı sesini kaydettiği varsayılmaz. Geçmiş gösterilecekse yalnız olay metadata'sı, izinli ses kaydı veya gerçekten mevcut transkript kaynakları temsil edilir.

### 4.1 Ana ekran öncelik hiyerarşisi

1. **Hazırlık**: model/yazılım/cihaz durumu, kritik blokaj.
2. **Birincil eylem**: konuşmaya başla, turu bitir veya bekle.
3. **Dinamik durum**: dinleniyor, işleniyor, ses oynatılıyor.
4. **Geri alma/kesme**: durdur, yeni tur, iptal.
5. **Ayrıntı**: yalnız kullanıcı açarsa süre, event ve teknik teşhis.

Kullanıcının konuşma sırasında menüyle boğuşması, küçük yazıları okuması veya model yapılandırması yapması istenmez. Audio session başladıktan sonra model değiştirme gibi yıkıcı eylemler disabled veya açıklamalı confirmation ile yönetilir.

## 5. Kaiwen Design System ile somut entegrasyon

Kaiwen Design ayrı ve mevcut bir React/TypeScript reposudur. 30 Ekim 2026 GitHub kod kontrolünde **`@imthekaiwen/ui-web`** paketi, `Button`, `Card`, `Tooltip`, `Input`, `Select`, `Switch`, `Checkbox`, `Modal`, `Drawer`, `ToastProvider`, `Alert`, `EmptyState`, `ErrorState`, `Skeleton`, `Spinner`, `Progress`, `AppShell`, `Sidebar`, `PageHeader`, `Wizard`, `KaiwenProvider` ve çeşitli layout primitive'lerini dışa aktarmaktadır. Paketin `0.2.0` kaynak sürümü ve `styles.css` public export'u doğrulanmıştır. Bu durum Live'ın o paketi başarıyla kurduğu veya npm registry erişiminin çalıştığı anlamına **gelmez**; lockfile ve gerçek install/build testi gereklidir.

**Gerçek kütüphane örnek kullanım iskeleti** (Kaiwen Design'ın mevcut public export isimleriyle; Live uygulaması henüz yazılmadı):

```tsx
import {
  KaiwenProvider,
  ToastProvider,
  Button,
  Card,
  type ThemePreference,
  type MotionLevel,
} from '@imthekaiwen/ui-web';
import '@imthekaiwen/ui-web/styles.css';

interface LiveRootProps {
  theme: ThemePreference;
  motion: MotionLevel;
  onStart: () => void;
  canStart: boolean;
}

export function LiveRoot({ theme, motion, onStart, canStart }: LiveRootProps) {
  return (
    <KaiwenProvider theme={theme} motion={motion} density="comfortable" locale="tr">
      <ToastProvider label="Bildirimler" dismissLabel="Bildirimi kapat">
        <Card>
          <Button type="button" disabled={!canStart} onClick={onStart}>
            Konuşmaya başla
          </Button>
        </Card>
      </ToastProvider>
    </KaiwenProvider>
  );
}
```

**Not:** Örnek mevcut Design import yüzeyini kullanır; Live'ın gerçek `onStart` event adapter'ı, state selector'ları, model ve mikrofon izin katmanı henüz yoktur. `onStart` uygulaması gerçek `capture.started` onayı gelmeden ekranı `listening` durumuna geçiremez.

| Live ihtiyacı | Gerçek Design bileşeni | Live'ın sahip olduğu katman |
|---|---|---|
| Birincil buton | `Button` | Mikrofon eylemi ve runtime çağrısı |
| Durum paneli | `Card`, `Alert` | Gerçek session state'inden görünüm |
| Cihaz seçici | `Select` | OS cihaz kimlikleri, format negotiation |
| Gizlilik ayarı | `Switch`, `Checkbox` | Persist, açık izin, policy enforcement |
| Onay penceresi | `Modal` | Ses kaydını saklama veya model değiştirme onayı |
| Kısa bilgilendirme | `Tooltip`, `ToastProvider` | Hata ve başarı bildirimleri |
| Model kurulumu | `Progress`, `Wizard` | Gerçek indirme / doğrulama yüzdesi |
| Uygulama kabuğu | `AppShell`, `Sidebar`, `PageHeader` | Navigasyon ve odak yönetimi |
| Mikrofon seviyesi/waveform | **Hazır Design bileşeni değil** | `AudioLevelMeter` / `VoiceActivityView` Live içinde |
| Konuşma durum makinesi | **Hazır Design bileşeni değil** | `ConversationController` Live içinde |

**Yasak:** Bir sayfa için `Button2`, `NewSwitch`, özel tema sağlayıcısı veya Design paketinin kopyalanmış kaynak ağacı oluşturmak. Yeni ortak parça ancak birden fazla Kaiwen uygulamasının ihtiyaç duyduğu, kararlı ve erişilebilir public API tasarımıyla Design'a taşınabilir.

## 6. Görsel dil — sakin, premium, işlevsel

Kaiwen Live'ın temel görünümü açık ve koyu temada **monokrom** kalır. Vurgu yüzeylerinin çoğu siyah, beyaz ve nötr grilerden gelir. Renk, tekil anlamlı durumlarda semantik kullanılır: hata, uyarı, gerçekten doğrulanmış başarı veya izin gereksinimi. Durum bilgisinin yalnız renk/animasyonla iletilmesi yasaktır.

**Hedef görsel yön:** açık alanda ferah yüzey, güçlü ama az sayıda başlık, geniş alt boşluklar, tek merkezi ses odağı; koyu temada saf siyaha gömülmeyen yüzey ayrımı ve okunur ikincil metin. Çok katmanlı cam, ağır blur, hareketli arka plan, devasa gradient veya gözü izleyen dekoratif efektler V1'in dili değildir.

### 6.1 Tokenlara bağlı kalma

Kaiwen Design semantik CSS değişkenlerini ve sağlayıcılarını kullan. `--kw-*` alanı kit ile gelir; ürün tarafında doğrudan sert kodlanmış renk dizileri yaratma. Kritik status bileşenleri kitin `status.error`, `status.warning` gibi anlamsal tokenlarına göre hazırlanır. Tema değişiminde beyaz/koyu yüzeyler, sınırlar ve tipografi otomatik tutarlı kalır.

**Önerilen optik tasarım ölçüleri** yeni Design tokenu değildir: rahat bir ana panel için yaklaşık 560–760 px maksimum okunabilir genişlik; desktop uygulama için 1000–1280 px başlangıç pencere aralığı; basılabilir kontrol hedefleri rahat etkileşime yetecek kadar geniş; gerçek değerler Windows DPI (%100/%125/%150/%200) ve erişilebilirlik testleriyle netleştirilir. Sabit piksel ölçüleri cihaz sorumluluğuna bağlanmalıdır; anlık mock değerlerini evrensel standart ilan etme.

### 6.2 Tipografi

- Türkçe karakterler (`ğ`, `ı`, `ş`, `ö`, `ü`, `ç`, büyük `İ`) tüm state ve toast örneklerinde test edilir.
- `İşleniyor…`, `Mikrofon kapalı`, `Model hazır` gibi durumlar 12 px seviyesine sıkıştırılmaz; ana durum görünür ve kısa olur.
- Metin azlığı, açıklama eksikliği değildir: gerektiğinde ikinci satırda nasıl düzeltileceği yazılır.
- Zaman, buffer sayıları ve metrikler tabular numerals kullanır; UI "sayılıp duran" görünmez.
- Gizli teknik identifier kullanıcıya ana başlık olarak sunulmaz; hata kodu kopyalanabilir detay panelindedir.
- Sistem fontuna ve okunabilir fallback'a öncelik ver; ticari veya özel fontlar izinsiz paketlenmez.

### 6.3 İkonografi

İkonlar `@imthekaiwen/icons` veya Design'ın yönettiği Lucide temelli yüzeyden gelir. Uygun işaretler: mikrofon, mic-off, kulaklık, volume, stop, refresh, settings, alert, check. Kaynağı belirsiz emoji, çeşitli icon kitleri, renkli marka sticker'ları veya dekoratif ses karakterleri yoktur. Icon-only düğmeler, erişilebilir ad ve tooltip taşır. `MicOff` ikonu tek başına mikrofon izninin reddedildiğini, kapandığını veya kullanıcının sessize aldığını karıştırmamalıdır.

## 7. Motion sistemi ve hareket bütçesi

Mevcut Design `@imthekaiwen/motion` paketinde `off`, `subtle`, `balanced`, `expressive` seviyeleri ve `prefers-reduced-motion` önceliği vardır. Kaiwen Live varsayılan olarak **`balanced`** kullanır. OS reduced-motion seçimi her zaman üstündür. Bir cihazda düşük FPS veya aşırı GPU yükü görülüyorsa Live, kullanıcı açıklaması ve açık ayarla hareketi `subtle`/`off` düzeyine alabilir; bu performans davranışı ölçülüp doğrulanmalıdır.

| Görsel olay | Hedef hareket | Ne zaman yapılmamalı? |
|---|---|---|
| Mikrofon aktif olduğunda | Kısa opaklık ve kontur geçişi | OS izin sonucu gelmeden |
| Ses seviyesi artınca | Hafif ve sınırlı meter yüksekliği | Ses verisi gelmiyorsa rastgele hareket |
| Model yüklenirken | Gerçek progress veya indeterminate spinner | İndirme durmuşsa hâlâ ilerliyormuş gibi |
| Yanıt başladı | Soft state transition | İlk PCM gerçekten oynatılmadan "Ses oynuyor" anlatımı |
| Kullanıcı durdurdu | Hemen görünür stop/idle etkisi | Uzun ve iptali geciktiren flourish |
| Hata oluştu | Kısa, dikkat çekici ancak sabit feedback | Sonsuz kırmızı yanıp sönme |
| Tema değişti | Hafif yüzey adaptasyonu | Reduced-motion veya perf sıkıntısı varsa |

**Motion hiçbir zaman gerçek audio callback'i sürmemelidir.** Waveform renderer'da Canvas/DOM ile çizilse bile kaynak veri bounded ve düşük oranlı ses metrikleridir. 24 kHz PCM'nin her örneği React state'ine yazılmaz. Hareket için requestAnimationFrame veya kontrollü frame cadence kullanılabilir; ancak bu yalnız **UI çizimi** içindir ve ses capture/oynatma zamanlayıcısının yerine geçmez. Renderer ağırlaştığında gösterge eksik frame atlayabilir, gerçek ses işleme engellenmemelidir.

### 7.1 Waveform fiziği — gerçeğe bağlı görsellik

Giriş seviyesi: gerçek `RMS` ve `peak` değerlerinden normalizasyon, yumuşatma ve attack/release eğrisi ile üretilir. Sessizlikte meter sıfıra yaklaşır. `microphone muted`, `permission denied`, `device absent` durumunda rastgele "dinleniyor" animasyonu yasaktır. Model konuşurken giriş ve çıkış göstergeleri farklı kaynaklar taşır; output waveform varsayılan olarak model PCM enerjisinden ölçülür. Model üretmiyorsa sahte sohbet dalgası yaratılmaz.

Önerilen UI ses metrik yayını sınırı: örneğin 15–30 Hz; bu yalnız hipotezdir, cihaz testinde seçilir. Her gerçek audio chunk'ının renderer'a gönderilmesi ek yük ve IPC tıkanıklığı yaratır; UI için düşük çözünürlüklü seviyelerin hesaplanması ayrı tutulur.

### 7.2 Reduced motion tasarım gereği

`prefers-reduced-motion: reduce` etkin olduğunda sürekli titreşim, pulse, spring bounce ve parallax kaldırılır. Bunun yerine statik ikon, görünür metin ve erişilebilir durum alanı kalır. İzin ya da konuşma durumunun anlaşılması hareketten bağımsız olmalıdır. UI testi reduced-motion ekranında da konuşmaya başlama/bitirme ve hata kurtarma senaryolarını kapsar.

## 8. Konuşma ekranı — birincil ürün yüzeyi

**Hedef düzen:** üstte küçük marka ve aktif model adı; merkezde "Hazır / Dinleniyor / Yanıt hazırlanıyor / Konuşuyor" durumu; altında gerçek ses seviyesi göstergesi; alt orta bölgede büyük ana eylem; en altta küçük cihaz/izin ve gizlilik metni. Birden fazla önemli eylem varsa ikincil butonlar belirgin ama geride kalır.

```text
┌───────────────────────────────────────────────────────────┐
│ Kaiwen Live                       [Model]   [Ayarlar]      │
│                                                           │
│                                                           │
│                    [ Gerçek ses meter ]                   │
│                      Hazır — Türkçe                       │
│             Mikrofonu açarak konuşabilirsin.              │
│                                                           │
│                    [ Konuşmaya başla ]                    │
│                                                           │
│             Mikrofon: Seçili giriş cihazı                 │
│              Ses yerel olarak işlenir.                    │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

Bu ASCII çizim piksel-perfect tasarım değil, **bilgi hiyerarşisi şemasıdır**. Uygulama ilk çalıştığında model bulunmadıysa aynı alan şöyle bir blokaja dönüşür: `Model gerekli` → `Yerel model seç` → desteklenen dosya paketini belirt. Model yüklenirken kullanıcı konuşma butonuna basamaz; fakat `Ayarlar` ve `İptal` kullanılabilir.

### 8.1 Konuşma alanının semantik bölgeleri

- `Main`: ana konuşma eylemi ve açıklaması.
- `StatusRegion`: salt gösterim; backend event'lerinden türetilen durum.
- `VoiceLevelMeter`: gerçek mikrofon veya model output seviyesi; dekoratif değil.
- `PrimaryAction`: duruma göre label değişen native button.
- `SecondaryActions`: playback durdur, yanıtı iptal et, yeni tur; yalnız uygun state'te.
- `DeviceSummary`: aktif aygıt; cihaz değiştirme ayarlara yönlendirir.
- `PrivacySummary`: yerel çalışma, kayıt politikası, varsa açık aktif aktarım.
- `NotificationRegion`: kısa hata/başarı mesajları; screen reader live region ile uyum.

### 8.2 Birincil eylemin bağlamsal değişimi

| Runtime durumu | Birincil eylem | İkincil eylem | Teknik koşul |
|---|---|---|---|
| `created` | Hazırlanıyor… (disabled) | Model/cihaz ayrıntısı | Session initialize başlamış |
| `initializing` | Hazırlanıyor… (disabled) | İptal (destekleniyorsa) | Henüz runtime ready değil |
| `ready` | **Konuşmaya başla** | Cihaz seçimi | Model ve mikrofon açılabilir |
| `listening` | **Konuşmayı bitir** | Mikrofonu kapat / sessize al | Capture gerçekten başladı |
| `processing` | Yanıt hazırlanıyor… | Yanıtı iptal et | Üretim sürüyor, ses henüz çalmıyor |
| `speaking` | **Yanıtı durdur** | Yeni tur (capability koşullu) | Gerçek playback başladı |
| `closing` | Kapatılıyor… (disabled) | — | Resource release bekleniyor |
| `closed` | Yeni oturum aç | Ayrıntılar | Kaynaklar bırakıldı |
| `failed` | Yeniden dene | Tanılamayı aç | Hata kodu ve öneri mevcut |

Bu tablo görünür metnin **yalnız genel session state'ten türetilmesini** dayatmaz. Bir session `speaking` olabilir fakat OS aygıtı çalmıyorsa `playback_error` durumuna geçer. `processing` durumunda ilk token üretildi diye `speaking` yazılmaz. Audio level ve playing state OS playback telemetry ile eşleştirilir.

## 9. Birincil mikrofon düğmesi ve klavye etkileşimi

**V1 kararı:** Click/tap ile **toggle**: durgun durumda `Konuşmaya başla`, dinlerken `Konuşmayı bitir`. Push-to-talk modu ancak gerçekten istenirse ayrıca eklenir; kısa basma ile uzun basma semantik olarak karıştırılmaz. Temel konuşma akışı fare gerektirmez.

Önerilen klavye kısayolu: odak güvenliği sağlanırsa `Space` veya `Ctrl+Space` ile konuşma; fakat `Space`, normal odaklı Button/Slider ve metin alanlarının doğal davranışını bozuyorsa global hotkey yapılmaz. Açık pencere ve erişilebilir focus durumları için `Ctrl+Space` gibi çakışmasız bir kısayol tercih edilmeden önce Windows/IME çakışmaları test edilir. İlk V1'de global OS kısayolu zorunlu değildir.

**Görsel durum:** Button `loading=true` durumuna yalnız beklenen belirli async eylem için girer; `disabled` microfon izni yokken veya model hazır değilken açıkça anlatılır. `aria-label` ekranda görünen eylemle uyumludur. Uzun basma, ayrı kullanıcı tarafından seçilmediği sürece gizli bir eylem tetiklemez.

### 9.1 İptal semantiği ve iki aşamalı karar

1. Kullanıcı **yanıtı durdur** derse Live playback queue'sunu yerel olarak hemen durdurur; arka plandaki generation için de `cancel_generation` gönderir ve geç yanıtları generation/epoch kontrolü ile reddeder.
2. Kullanıcı **mikrofonu kapat** derse yalnız capture kaynağını kapatma veya ilgili audio turn'u bitirme protokolü uygulanır; model generation'ı dolaylı ve belirsiz şekilde iptal edilmiş sayılmaz.
3. Kullanıcı **oturumu kapat** derse tüm owned kaynaklar kapatılır; UI `closed` doğrulaması gelene kadar yeni session başlatmayı sınırlayabilir.
4. Kullanıcı **oynatmayı sustur** derse model üretiminin devam etmesi veya iptali ürün politikasına bağlı açık seçilir; `stop_playback` tek başına `cancel_generation` değildir.

**Temel hata örneği:** Kullanıcı konuşmayı keser, ekranda `Hazır` görünür, fakat eski PCM tekrar çıkarsa bu yalnız görsel kusur değil, **kritik kullanıcı kontrolü ihlalidir**. Red testi ve event trace zorunludur.

## 10. Görsel session state machine ve event kaynakları

Backend session durumları [Architecture](ARCHITECTURE.md) ve [Workspace Integration](../../docs/INTEGRATION.md) ile eşleştirilir. Görünür UI state, event'lerin sığınağı olan tek bir reducer/store tarafından türetilmelidir. Component'ler kendi başına `setIsListening(true)` yaparak gerçekliği uyduramaz.

**Hedef görünüm modeli** (tipler uygulama içi örnek, mevcut Live kodu değildir):

```ts
export type LiveViewMode =
  | 'setup_required'
  | 'starting'
  | 'ready'
  | 'listening'
  | 'processing'
  | 'speaking'
  | 'recovering'
  | 'failed'
  | 'closing';

export interface LiveViewState {
  mode: LiveViewMode;
  sessionId: string | null;
  sessionEpoch: number;
  turnId: string | null;
  generationId: string | null;
  microphonePermission: 'unknown' | 'granted' | 'denied';
  captureActive: boolean;
  playbackActive: boolean;
  modelReady: boolean;
  nativeStreamingAvailable: boolean;
  currentInputDeviceId: string | null;
  currentOutputDeviceId: string | null;
  errorCode: string | null;
}
```

**Kural:** Yukarıdaki state `processing`, `speaking`, `listening` vb. UI gösterimidir; IPC protokolündeki `session.state_changed`, `capture.started`, `playback.started`, `generation.cancelled` gibi event isimleri ancak final transport sözleşmesi onaylandıktan sonra kesinleşir. Bir görsel durum için gelen geç olay, güncel `session_epoch` / `generation_id` ile uyuşmuyorsa reducer onu reddeder.

### 10.1 State değişimlerinin doğruluk tablosu

| Olay | Beklenen UX | Yapılmayacak şey |
|---|---|---|
| Kullanıcı konuşmaya başlar | Geçici `Mikrofon açılıyor…` | Olay gönderildi diye `Dinleniyor` yazma |
| Capture açıldı | `Dinleniyor` + gerçek input level | Son ses seviyesini tekrar tekrar oynatma |
| Tur sonlandırıldı | `Yanıt hazırlanıyor…` | Input buffer boşsa başarılı turn ilan etme |
| Generation başladı | `Yanıt hazırlanıyor…` | Görünür token sayısını "ses çalıyor" diye kullanma |
| İlk PCM hoparlör cihazına gönderildi | `Ses çalınıyor` veya platform ölçümüne göre `Konuşuyor` | OS sample ilk çalmadan kesin TTFA iddiası |
| Playback bitti | `Hazır`/uygun sonraki state | Son buffer hâlâ çalınıyorsa erken bitirme |
| Generation iptal edildi | İptal teyidi, son generation filtrelenir | Eski PCM buffer'ını koruma |
| Sidecar öldü | `Bağlantı kesildi` + retry | Sessizce sonsuz spinner |
| İzin reddedildi | `Mikrofon izni gerekli` | Sahte audio activity gösterimi |

### 10.2 Event şeması örneği — hedef

```json
{
  "protocol_name": "kaiwen.live.session",
  "protocol_version": "1.0.0",
  "event_id": "evt-0042",
  "session_id": "sess-local-01",
  "stream_id": "stream-audio-01",
  "sequence": 42,
  "event_type": "capture.started",
  "occurred_at_utc": "2026-10-30T12:00:00Z",
  "monotonic_ns": 1938435290,
  "correlation_id": "corr-01",
  "payload": {
    "device_id": "default-input",
    "sample_rate": 24000,
    "channels": 1
  }
}
```

Bu JSON örneği **tasarlanan olay biçimidir**, gerçek uygulamadan yakalanmış olay değildir. `stream_id`, `sequence` ve monotonic clock alanları belirtilen [Integration](../../docs/INTEGRATION.md) sözleşmesine uyar. Gerçek üretimde duvar saati ve monotonic zaman farklı amaçlara hizmet eder; süre hesabında uygun monotonic referanslar kullanılmalıdır.

## 11. İlk çalıştırma / onboarding

İlk sürümde onboarding en fazla üç karar adımına bölünür; kullanıcı hangi modelin kurulacağını ve sesin nereye gittiğini anlayabilmelidir. Bir marka tanıtımı veya sonsuz özellik turu yoktur.

**Adım 1 — Yerel model:** Geçerli Forge release doğrulaması olan model seçilir; model yoksa yerel dosya ekleme veya izinli indirme gösterilir. Model indirme ağ kullanacaksa bu açıkça belirtilir. Eğitim checkpoint'inin doğrudan stable release olarak tanınmasına izin verilmez.

**Adım 2 — Ses cihazı:** Mikrofon ve çıkış cihazı listelenir; kullanıcı seçimi, cihaz capabilities ve örnek test ile doğrulanır. OS izni cihaz açılırken istenir; iznin neden gerektiği önce kısa anlatılır. Mikrofon izni yoksa "Ayarlar'da izin ver" yönlendirmesi sunulur.

**Adım 3 — Deneme konuşması:** Demo mümkünse gerçek speech path ile yapılır. Model henüz çalışmıyorsa yalnız test tone veya loopback çalıştırılır ve bunun **ses cihazı testi** olduğu açıkça belirtilir. "Modelle konuştun" denmez.

**Onboarding tamamlandı** sayılması için cihaz, model ve gizlilik seçenekleri anlaşılıp saklanmış olmalıdır; ilk sesli turun bilimsel kalitesi garanti değildir. Kullanıcı sonradan her ayarı yeniden açabilmelidir.

### 11.1 Model indirme ve paketleme ekranı

İlerleme göstergesi `indeterminate` veya gerçek byte sayaçlı `determinate` şeklinde çalışır. Sırf kullanıcı bakarken gösterge ilerliyor izlenimi vermek için rastgele yüzde üretilmez. `İndiriliyor` → `Dosya doğrulanıyor` → `Codec uyumluluğu kontrol ediliyor` → `Model yükleniyor` birbirinden ayrılır. Bir aşama başarısız olduğunda kopyalanabilir hata kodu ve `Yeniden dene` bulunur; eski çalışan model otomatik silinmez.

### 11.2 Offline ilk açılış

İnternet yoksa uygulama normal olarak açılabilir. Yerel model varsa session başlatılır. Model yoksa "Model bulunamadı; yerel paket ekleyin" mesajı gösterilir. Offline kullanıcıya tekrar tekrar ağ izni isteyen veya yanıt vermeyen bir buton sunulmaz. Agent/retrieval gerektiren ileri özellikler offline durumunu ayrıca belirtir.

## 12. Mikrofon izinleri ve donanım durumu

İzinleri Live ürünü yönetir; renderer izin varmış gibi varsaymaz. Windows işletim sistemi ve seçilen native audio backend'in izin modeli dikkate alınır. İzin reddedildiğinde UI yeni istekleri spam'lemez; kullanıcıya hangi ayarı açacağı ve uygulamaya dönünce nasıl yenileyeceği anlatılır. İzin onayıyla fiziksel cihaz açılmasının farklı sonuçlar olduğu unutulmaz.

| Durum | Kısa mesaj | Kullanıcı eylemi |
|---|---|---|
| OS izni verilmemiş | `Mikrofon izni gerekli` | `Windows ayarlarını aç` (destekli ve doğrulanmış yol) |
| Seçilen cihaz çıkarılmış | `Mikrofon bağlantısı kesildi` | `Başka mikrofon seç` |
| Cihaz başka uygulamada kullanımda | `Mikrofon açılamadı` | `Yeniden dene`, cihaz değiştir |
| Input boş/sessiz | `Ses algılanmıyor` (gerçek sinyal ölçümüyle) | `Mikrofonu test et` |
| Çıkış cihazı yok | `Ses çıkışı bulunamadı` | `Hoparlör seç` |
| Çıkış ses seviyesi kapalı | `Ses duyulmuyor olabilir` | Ses testini çalıştır |
| Format uyuşmuyor | `Cihaz biçimi desteklenmiyor` | Uygun cihaz veya resampling politikası |
| Hotplug ile yeni cihaz | Sessiz otomatik seçim yerine bilgilendirme | Kullanıcıya mevcut oturumu sürdürme seçeneği |

**Güvenlik sınırı:** `Windows ayarlarını aç` gibi OS eylemleri doğrudan renderer `shell.openExternal` yetkisiyle değil, allowlist'li preload→main köprüsü ve sabit onaylı URI üzerinden yapılır. Kullanıcıdan gelen keyfî shell URI'si çalıştırılmaz.

### 12.1 Cihaz testinin güvenilirliği

Mikrofon testinde ses seviyesi göstergesi gerçek alınmış audio'yu temsil eder; kullanıcı isterse **kısa yerel loopback** dinleyebilir. Loopback açıkken feedback/echo riski anlatılır, ses varsayılan olarak diske yazılmaz, cihaz testinden çıkınca audio stream kapatılır. Test mode audio stream'i gerçek model session'a sızmaz.

Hoparlör testi için telifsiz, kısa, uygulamayla birlikte paketlenen test sesi veya programatik üretilmiş test tonu kullanılır. Ürün bunu model yanıtı diye göstermemelidir. Ses çıkışı onayı gerçek cihaz playback durumuyla eşleşmelidir.

## 13. Model yönetimi UX'i

Model ekranında minimal liste: model adı, release sürümü, yaklaşık disk boyutu, doğrulama durumu, codec adı ve numarası, kullanabileceği runtime yetenekleri ve aktif/stable/experimental etiketi. Kullanıcı yanlış modelin neden seçilemediğini anlamalı; "uyumsuz" kelimesinin yanında açıklama olmalıdır.

**Model ekleme akışı:** Dosya seç → manifest oku → izinli dizine güvenli kopyala/stage → SHA-256 doğrula → codec ve Speech SDK gereksinimini kontrol et → bellek tahminini göster → aktive et. Dosya seçimi otomatik aktivasyon değildir. Doğrulanmayan paket yüklenmez. `model_ready` olayı gelmeden konuşma butonu açılmaz.

**Aktif görüşme sırasında değişim:** Önce oturum kapatma ve o turdaki sesin durması gerekir. UI bu etkiyi açıkça gösterir: "Modeli değiştirmek mevcut konuşmayı bitirecek." Onay olmadan conversation state yakılmaz. Yanlış model yüklenirse eski doğrulanmış release otomatik korunur; rollback kullanıcıya görünür bir recovery eylemi olarak sunulur.

### 13.1 Bellek kapasitesi bilgisi

`2 GB VRAM hedefi` mevcut ürün garantisi değildir. UI modelin teorik ağırlık boyutunu gösterebilir, fakat bu toplam runtime VRAM anlamına gelmez. Yeterli VRAM yoksa backend'in gerçek load hatası gösterilir ve doğrulanmış daha küçük model veya CPU modu **gerçekten destekleniyorsa** önerilir. FPS, TTFA, RTF veya RAM tahminleri benchmark profili olmayan cihazlarda "ölçülmedi" olarak görünür.

## 14. Yanıt çalma ve sesli geribildirim

Kullanıcının duyduğu ses, UI'daki `speech` state'inin ana doğrulama noktasıdır. Yanıt başladığında küçük bir output seviye göstergesi çalışabilir; ses çıkışı sessizse audio device durumu ayrıca incelenir. Model token üretirken fakat codec decode başarısızken kullanıcı `Yanıt hazırlanıyor` veya ilgili hata mesajını görür; `Konuşuyor` yazılmaz.

**Oynatma kontrolleri:** V1'de `Yanıtı durdur`, `Tekrar dene` (yalnız güvenli replay/generation semantiği mevcutsa) ve yeni tur. Önceki response PCM RAM'de tutulmuyorsa `Tekrar oynat` kontrolü bulunmaz; yeni inference ile replay aynı şey değildir ve kullanıcıya saklama hakkında yalan söylenmez.

Oynatma tamponu boşalırsa `ses çalıyor` görünümünü sonsuza kadar sürdürme. Underrun kısa ise olayı sessizce düzeltebilir; tekrarlıyorsa `Ses kesiliyor` uyarısı ve Tanılama'da buffer/RTF verileri gösterilir. Kullanıcı konuşmaya girdiğinde, desteklenen barge-in politikasına göre model yanıtının kesileceği açık biçimde anlatılır.

### 14.1 Barge-in / kesinti deneyimi

- Kullanıcı konuşurken model sesi oynuyorsa yalnız desteklenen input detection durumunda otomatik kesme açılabilir. V1'de kullanıcı butonla manuel `Yanıtı durdur` yapabilmelidir.
- Echo cancellation garanti değilse model sesi otomatik kullanıcı konuşması sanılabilir. Bu riski saklamak yerine manual interruption default seçilebilir.
- Sesin kesilme animasyonu 200 ms sürse bile PCM playback stop eylemi animasyon bitişine bağlanamaz.
- Yeni generation açılmadan önce eski `generation_id` iptal veya stale filter ile güvenli hâle getirilir.
- Screen reader'a her PCM chunk için duyuru yapılmaz; yalnız "Yanıt durduruldu" gibi önemli durumlar anons edilir.

## 15. İzinli kayıt, geçmiş ve gizlilik UX'i

**Varsayılan:** Ham mikrofon sesi, model output'u, metin dökümü veya kişisel konuşma transkripti kalıcı olarak kaydedilmez. İşlem sırasında RAM/OS buffer kullanımı olabilir; kullanıcıya "hiç belleğe alınmıyor" gibi yanlış bir vaat verilmez. Tanılama örneklerinde `audio_bytes` veya gizli konuşma içeriği görünmez.

İleride `Bu oturumu kaydet` özelliği açılırsa ayrı consent akışı gerekir: neyin kaydedildiği (input, output, transkript, sadece metadata), nereye kaydedildiği, ne kadar saklandığı, nasıl silindiği ve opsiyonel olarak şifrelenmesi belirtilir. Kaydetme açıkken kalıcı kayıt göstergesi sürekli görünür olmalıdır; uygulamayı yeniden başlatmak sessizce izin durumunu yükseltmez.

`Logları dışa aktar` işlevi gizlilik kontrolünden geçer: yalnız olay ID, hata kodu, device class/driver ve ölçümler; token, model indirme kimlik bilgisi veya ses bytes'ı yok. Gerekli teknik alanlar varsa kullanıcı export öncesi önizleme yapabilir. Uygulama beklenmedik ağ trafiği başlatıyorsa bunu "offline çalışma" etiketi altında saklayamaz.

### 15.1 Ajan yetkileri için yer tutucu

İlk Live UX'inde Agent ekranı zorunlu değildir. İleride eklenirse `web arama`, `dosya açma`, `uygulama çalıştırma` gibi her tehlikeli yetki açık bir action, görülebilir kaynak ve kullanıcı onayına dayanır. Agent'ın metin cevabının model tarafından doğrudan speech-native söylendiği iddia edilmez; gerekirse onaylı text-to-audio köprüsü ayrı gösterilir. İlgili tasarım daha sonra `AGENT_INTEGRATION.md` ile tanımlanacaktır.

## 16. Ayarlar sayfası ve temel kontrol sözleşmeleri

Ayarlar üç ana kategoriye odaklanır: **Ses**, **Görünüm**, **Gizlilik ve uygulama**. Sorun giderme detayları ayrı `Tanılama` görünümündedir. Her ayarın tipi doğru seçilir: ikili durum için Switch, birden çok cihaz için Select, bilgi için salt okunur Card, tehlikeli işlem için Modal onayı.

| Ayar | Kontrol | Kalıcılık | Yan etki |
|---|---|---|---|
| Giriş aygıtı | Select | Yerel | Capture yeniden açılması gerekebilir |
| Çıkış aygıtı | Select | Yerel | Output buffer yeniden bağlanabilir |
| Ses testini başlat | Button | Hayır | Kısa test / loopback |
| Tema | ThemeSwitcher/Select | Yerel | `light`, `dark`, `system` |
| Hareket düzeyi | Select | Yerel | `off`, `subtle`, `balanced`, `expressive` |
| Ölçüm paneli | Switch | Yerel | Debug metrics görünümü; audio capture başlatmaz |
| Kullanım verisi saklama | Switch / Modal | Kullanıcı izni şart | Varsayılan kapalı; policy tarafından sınırlandırılır |
| Model yükleme | Button | Artifact | Uyumluluk ve hash kontrolü gerekir |
| Fabrika ayarları | Destructive Button / Modal | Çok aşamalı | Kayıt/ayar silme kapsamı net anlatılır |

**Yanlış UI antipattern:** Toggle açılır açılmaz yeşile dönüp backend başarısız olsa bile açık kalması. Kontrollü Switch durumu yalnız başarılı policy persist veya cihaz operation ack sonrasında kesinleşir; optimistic UI kullanılacaksa rollback ve anlık hata açıklaması zorunludur.

### 16.1 Ayarların saklama sözleşmesi

Tercihler OS kullanıcı profiline bağlı, path traversal'a izin vermeyen bir konumda saklanır. Gizlilik ayarları UI içinde varsayılan değer gösterimiyle çelişmemelidir. Kullanıcının seçtiği var olmayan cihaz eski ID ile açılamazsa UI açıkca geçerli cihaz seçimine yönlendirir; rastgele cihazı mikrofona gizlice bağlamak yerine kullanıcıdan onay veya önceden bilinen politika gerektirir.

## 17. Hata, boş, bekleme ve kurtarma durumları

Her hata **nerede**, **ne olmuş**, **ne yapılabilir** üçlüsünü taşır. Bu metinler kısa kalır ama teknik olarak dürüst olur. Bir işlem sürerken kontrolün üzerinde `Loading…` yerine hangi aşamanın beklendiği görünür. Bir işlemin üst üste tetiklenmesi onay idempotency mekanizmasıyla veya disabled state ile engellenir.

| Durum | Ana başlık | Yardımcı metin / eylem |
|---|---|---|
| Model yok | `Henüz bir model seçilmedi` | `Yerel model ekle` |
| Codec uyumsuz | `Bu modelin ses codec'i uyumsuz` | `Desteklenen model sürümlerini görüntüle` |
| Mikrofon izni yok | `Mikrofon izni gerekli` | `Windows izinlerini kontrol et` |
| Mikrofon cihazı bulunamadı | `Mikrofon bulunamadı` | `Cihaz seç` |
| Hoparlör yok | `Ses çıkışı bulunamadı` | `Çıkış aygıtını seç` |
| Sidecar yanıt vermiyor | `Ses motoruna bağlanılamıyor` | `Yeniden dene`, `Tanılama` |
| GPU OOM | `Model için yeterli GPU belleği yok` | `Daha hafif model` (gerçekte varsa) |
| Model sessiz EOS döndürdü | `Model sesli yanıt üretemedi` | `Yeniden dene` |
| Audio underrun | `Ses kısa süre kesildi` | Gelişmiş ölçümler Tanılama'da |
| Model doğrulama başarısız | `Model paketi doğrulanamadı` | Hash/manifest nedenini detaydan göster |
| Network kapalı | `Çevrimdışı çalışıyorsun` | Yerel model ve özelliklerle devam |
| İndirme tamamlanamadı | `Model indirilemedi` | `Yeniden dene`, güvenli partial cleanup |
| Session kapatılıyor | `Oturum kapatılıyor` | Sabit spinner; işlem süresi sınırlı |
| Agent desteklenmiyor | `Araç kullanımı bu sürümde kapalı` | Konuşma deneyimi kullanılabilir kalır |

### 17.1 Doğru hata dili ve örnek mikro metinler

- **İyi:** `Mikrofon açılamadı. Başka bir uygulama cihazı kullanıyor olabilir. Cihaz seçimini kontrol edip yeniden dene.`
- **Kötü:** `Error 500: Audio failure.`
- **İyi:** `Model yüklendi, ancak konuşma başlatılamadı. Ses motorunu yeniden başlatabilirsin.`
- **Kötü:** `Her şey hazır!` (model yüklendiği halde capture başarısızsa).
- **İyi:** `Bu model native streaming desteklemiyor. Tek tur konuşma modunu kullanabilirsin.`
- **Kötü:** `Gerçek zamanlı konuşma aktif!` (yalnız batch generate varsa).

### 17.2 Recovery deneyimi

Hata durumunda eski session kimliği korunup görünür deney yeniden başlatılırken yeni `session_epoch` açılmalıdır. Ekran, yeniden bağlandığında geç gelen `playback.started` olayının kendisini yanlışlıkla konuşuyor hâline sokmasına izin vermez. Hata kodu üst katmandan gelen sınıflandırmaya göre eşleştirilir; GUI içinde keyfî string eşleştirme ile binlerce error varyantı üretme. Retry sayısı bounded olmalı ve yeniden denemeler arasında bekleme/durdurma imkânı tanınmalıdır.

## 18. Geri bildirim, toast, modal ve uyarı hiyerarşisi

| Durum | Görsel kanal | Sebep |
|---|---|---|
| Başarılı mikrofon açılışı | Ana durum satırı | Toast spam'i gerekli değil |
| Ayar kaydedildi | Kısa Toast | Kullanıcının tek seferlik eylemi |
| Model güncellemesi | Progress + durum | Uzun süren işlem, kalıcı alan |
| Cihaz kaybı | Inline Alert | Görev engellendi; toast kaybolmamalı |
| Model bozuk | ErrorState / panel | Eylem ve ayrıntı gerekir |
| Kaydı sil | Modal | Geri alınması zor işlem |
| Aktif modeli değiştir | Modal veya açık onay paneli | Görüşme kapanışı etkisi |
| Sıradan ses seviyesi | Meter, gerektiğinde caption | Her frame toast yasak |
| İptal tamamlandı | Ana durum satırı; gerektiğinde kısa Toast | Kritik işlem durumuna bağlı |

Ekran okuyucu `aria-live` duyuruları yalnız anlamlı state transition'larda yapılır. Çok sık gelen VAD/PCM olayları live region'a gönderilmez. Modal açıldığında focus trap, Escape davranışı, odak geri dönüşü ve destructive action onayı mevcut Design bileşen davranışlarına uyar.

## 19. Erişilebilirlik hedefleri ve test kapsamı

Hedef **WCAG 2.2 AA** seviyesinde test edilebilir arayüzdür; sadece "erişilebilir" ifadesi yazmak yeterli değildir. Windows ekran okuyucuları ve klavye kullanıcıları için ana ses akışı bağımsız olmalıdır.

**Zorunlu kontroller:**

- Birincil mikrofon eylemi, Space/Enter ile çalışır; global shortcut normali bozmaz.
- Mikrofon izni reddedildiğinde yalnız renk veya dalga değişikliği değil okunur metin vardır.
- Ekran okuyucu güncel ana durumu anlamlı aralıklarla alır; 30 FPS meter anonsu yoktur.
- Form input'ları görünür label'a, hata açıklamasına ve focus-visible işaretine sahiptir.
- Modal açıldığında odak uygun başlık/ilk eyleme gider, kapanınca mantıklı yere döner.
- Görünür metinler yeterli kontrasta sahiptir; disabled metin gereksiz okunamaz hâle gelmez.
- `prefers-reduced-motion` bütün nonessential animasyonları kaldırır.
- %200 yakınlaştırmada ana kontrol görünür, yatay taşma ve focus kaybı yaşanmaz.
- Windows %125/%150/%200 DPI ile uzun Türkçe metinler kırpılmaz.
- Pointer target ve klavye focus göstergeleri küçük teknik ikonlarda da belirgindir.
- Model ve mikrofon durumunu kullanıcı yalnız waveform hareketinden çıkarmak zorunda kalmaz.
- Hata mesajının geri dönme/yeniden deneme eylemi erişilebilir adıyla sağlanır.

**Ekran okuyucu örnekleri:** `Sesli asistan: Hazır. Konuşmaya başla düğmesi.` / `Mikrofon dinliyor. Konuşmayı bitir düğmesi.` / `Yanıt hazırlanıyor. Yanıtı iptal et düğmesi.` / `Yanıt durduruldu. Yeni konuşmaya başlayabilirsin.`. Bunlar önerilen Türkçe duyuru metinleridir; gerçek erişilebilirlik API çıktıları Playwright/axe ve Windows NVDA/ekran okuyucu denemeleri ile doğrulanmalıdır.

### 19.1 `aria-live` kapsam sınırı

Bir duyuru kuyruğu aynı state tekrarını engeller. `voice_level_changed` gibi sinyal olayları yalnız meter çizimini değiştirir. Model bir saniyede 50 frame üretse bile ekrandaki durumu 50 defa okuma davranışı yasaktır. Uzun süren işlemlerde uygun aralıkla anlamlı ilerleme duyurusu yapılabilir; UI yine kullanıcı onayını bekleyen bir cihaz iznini süresiz arka planda yürütmez.

## 20. Pencere boyutu, responsive davranış ve OS entegrasyonu

Hedef öncelikle **Windows laptop** ekranıdır. 1366×768 gibi sıradan çözünürlüklerde ana ses eyleminin ekran dışında kalması kabul edilmez; yüksek DPI ve çoklu monitör durumları test edilmelidir. Pencere boyutu değiştiğinde kontroller kırılmaz, dar genişlikte teknik paneller alt alta gelir, drawer/modal içerikleri scroll kazanır. Desktop responsive tasarım web'i taklit etmek zorunda değildir; OS pencere chrome, min/max, titlebar ve erişilebilir odak mekanikleriyle birlikte tasarlanır.

**Hedef responsive yaklaşım:** konumlandırma önce flex/grid ve semantic spacing ile; sabit üst üste bindirme yerine kapsayıcı sınırları. `min-width` uygulamanın temel kontrollerini korur ama küçük laptoplarda gereksiz geniş pencere zorunluluğu yaratmamalıdır. GPU infere ederken animasyon ve frontend bundle CPU bütçesi düşük tutulur.

**Gelişmiş sistem tepsisi V1 zorunluluğu değildir.** İleride eklenirse kullanıcı pencereyi kapattığında mikrofonun açık mı kalacağı açık politika ve görünür tray durumuyla tanımlanır. "Pencere kapandı ama uygulama sessizce dinlemeye devam ediyor" davranışı kabul edilmez.

### 20.1 OS mikrofon göstergesiyle tutarlılık

OS tarafından izin/aktif mikrofon göstergesi görünürken Live içindeki durum tersini söylüyorsa hata olarak ele alınır. Electron izinleri, native capture ve Windows sistem izinleri farklı katmanlarda olabilir; tek `permissionGranted` boolean'ı bütün gerçeği temsil etmez. `captureActive` yalnız gerçek başarı olayı ile belirlenir; kapanışta OS kaynağı bırakılmalıdır.

## 21. Konuşma geçmişi, transkriptler ve veri gösterimi

Speech-native mimari **otomatik metin transkripti üretmek zorunda değildir**. Bu yüzden geçmiş paneli tasarımı belirli konuşma cümlelerini gerçekmiş gibi uydurmamalıdır. Eğer bir ASR araç katmanı ayrıca çalıştırılırsa metnin kaynağı ve doğruluk durumu açık görünür; ana sesli yanıt modelinin çıktılarına gizlice eşlenmiş kesin transkript olarak sunulmaz.

**V1 mevcut oturum görünümü:** en fazla kısa tur meta bilgisi; `Kullanıcı sesi: 4,2 sn`, `Yanıt: 2,8 sn`, durum/hata. Bu süreler yalnız ölçüldüyse gösterilir. Ham ses varsayılan olarak saklanmadığı için uygulama yeniden açıldığında eski konuşmaların sesli replay'i otomatik olamaz. Sonraki sürümlerde onaylı kayda alma ve saklama politikası ayrıca tasarlanır.

**Audio-first debug:** Test sırasında segment ID ve PCM süreleri tanılamada kullanılabilir. Son kullanıcı ekranına uzun hex hash veya JSON basılması kullanılabilirliği düşürür. Bilgi seviyeleri rol tabanlı değil, bağlama göre aşamalı açılır: basit durum → ayrıntılar → kopyalanabilir teknik hata.

## 22. Tanılama ekranı — görünür ve doğru ölçümler

Tanılama ekranı yalnız gerçekten alınmış runtime ölçülerini gösterir. Henüz ölçülmemiş değerler `— / Ölçülmedi` şeklindedir. Modelin 2 GB hedefi veya gecikme iddiası bir tasarım mockup'ındaki sayıdan türetilmez.

| Ölçü | Kimin ölçmesi gerekir? | Ekranda etiket |
|---|---|---|
| İlk token süresi | Speech runtime | `İlk token (ms)` |
| İlk decode PCM | Speech runtime | `İlk ses üretimi (ms)` |
| İlk oynatılabilir PCM | Playback queue | `Çalınabilir ses (ms)` |
| İlk duyulan/cihaza verilen ses | OS audio layer | `İlk oynatma (ms)` |
| RTF | Speech/runtime | `Gerçek zaman faktörü` |
| Peak allocated VRAM | GPU backend | `Peak allocated GPU` |
| Peak reserved VRAM | GPU backend | `Peak reserved GPU` |
| Output underrun | Device playback | `Ses boşlukları` |
| Input dropped chunks | Capture/transport | `Düşen ses parçaları` |
| Sidecar restart | Process supervisor | `Motor yeniden başlatmaları` |
| Session epoch | Session actor | `Oturum nesli` |
| Frame FPS | Renderer profiler | `Arayüz FPS` |

`TTFA` teriminin her yerde aynı ölçüm olayıyla eşleştirilmesi zorunludur. UI metrikleri için tek ölçüm API'si yapılır. Kullanıcı bir değeri dışa aktarırken cihaz adı/ID gibi bilgilerin gizlilik riski değerlendirilir. Ekranda görünür ondalık basamakları gerçek sensör/model ölçümünün çözünürlüğünü aşmamalıdır.

### 22.1 Örnek diagnostics modeli — HEDEF

```json
{
  "schema_version": "1.0.0",
  "session_id": "sess-local-01",
  "timestamp_utc": "2026-10-30T12:00:10Z",
  "runtime_mode": "batch",
  "model_release": "candidate-local-01",
  "first_token_ms": null,
  "first_playable_audio_ms": null,
  "first_playback_ms": null,
  "rtf": null,
  "gpu_peak_allocated_bytes": null,
  "input_dropped_chunks": 0,
  "output_underruns": 0,
  "measurement_status": "not_measured"
}
```

Örnek bir fixture'dır. `null` alanları başarısızlık ya da sıfır olarak gösterilmez; `Ölçülmedi` açıklamasına karşılık gelir. Gerçek diagnostics kaydı otomatik olarak konuşmanın ham sesini, kullanıcı kimliğini veya Agent gizli verisini içermez.

## 23. Telemetry, performans ve UI rendering bütçesi

Amaç bütün kullanıcı etkileşimlerinin kesintisiz kalmasıdır. Mikrofonun sesini yakalayan thread/UI arasında ağır hesaplama paylaşılmaz. Renderer kendi çerçevelerini düşürebilir fakat audio callback bloklanamaz. Event ingestion ile React state update'leri coalesce edilir: 50 Hz/100 Hz audio event'i varsa UI aynı hızla tüm component ağacını yeniden render etmek zorunda değildir.

**Önerilen ölçüm hedefleri** proje kabulü için başlangıç araştırma bütçeleridir, test sonucunu temsil etmez:

- İleri seviye görseller olmadan basit bir durum değişiminde kullanıcıya belirgin gecikme yaratmamak.
- Ses level meter UI güncellemesi 15–30 Hz deneyi; gerçek sample rate ile asla eşitleme.
- Ana eylem feedback'ini network/GPU yüküne rağmen hızlı göstermek, ancak sonucu erkenden doğru ilan etmemek.
- Model yükleme süresince UI'nin menü, focus, `İptal` ve pencere kapatma eylemlerine yanıt verebilmesi.
- Cihaz değişimi/sidecar restart sırasında CPU spike ve memory leak ölçmek.
- Uzun oturumda DOM node, event listener ve JS heap büyümesini izlemek.
- Reduced-motion'da pahalı waveform/canvas süslemelerini kapatabilmek.

**Kabul metriği tanımı:** FPS tek başına ses kalitesini ölçmez. Frame timing, dropped UI frames, audio buffer underrun, mic dropped samples ve TTFA farklı metriklerdir. Birini iyileştirirken diğerinin gerilediği deneyler birlikte raporlanır.

## 24. Arayüz bileşen mimarisi

Live'a özgü komponentler ince tutulan ürün katmanında kalır. Audio runtime state'i komponentlere dağılmaz. Domain state bir typed controller/reducer üzerinden gelir. UI component'i yalnız state + handler tüketir. Dizinin adı ve dosyalar **HEDEF** örnektir; GitHub'da mevcut değildir.

```text
apps/desktop/src/
├── app/
│   ├── App.tsx
│   ├── AppProviders.tsx
│   └── routes.tsx
├── features/
│   ├── conversation/
│   │   ├── ConversationPage.tsx
│   │   ├── PrimaryVoiceAction.tsx
│   │   ├── ConversationStatus.tsx
│   │   ├── AudioLevelMeter.tsx
│   │   └── conversationSelectors.ts
│   ├── models/
│   │   ├── ModelsPage.tsx
│   │   ├── ModelCard.tsx
│   │   └── ModelImportWizard.tsx
│   ├── devices/
│   │   ├── DevicePicker.tsx
│   │   └── DeviceTestPanel.tsx
│   ├── settings/
│   │   ├── SettingsPage.tsx
│   │   └── PrivacySettings.tsx
│   └── diagnostics/
│       ├── DiagnosticsPage.tsx
│       └── MetricsSummary.tsx
├── state/
│   ├── liveStore.ts
│   ├── liveReducer.ts
│   └── selectors.ts
├── adapters/
│   └── runtimeBridge.ts
└── styles/
    └── live.css            # yalnız Live ürününe özgü düzen ve sınırlı token override
```

`AudioLevelMeter` Canvas veya hafif DOM renderer kullanabilir; ilk tercih karmaşık bir WebGL/Three.js animasyon motoru değildir. Görsel component tek başına mikrofon istemez; audio metric prop alır. `DevicePicker` OS cihaz listesine bağımlıdır ama backend IPC çağrısını içindeki CSS'e bağlamaz.

### 24.1 Component prop sözleşmesi — hedef

```ts
export interface AudioLevelMeterProps {
  rms: number | null;
  peak: number | null;
  active: boolean;
  kind: 'input' | 'output';
  reducedMotion: boolean;
  label: string;
}

export interface ConversationStatusProps {
  title: string;
  description?: string;
  tone: 'neutral' | 'info' | 'success' | 'warning' | 'error';
  busy: boolean;
}

export interface PrimaryVoiceActionProps {
  label: string;
  onActivate: () => void;
  disabled: boolean;
  busy: boolean;
}
```

Bu örnekteki `rms`, `peak` değerleri **normalize edilmiş UI metrikleridir**. Varsayılan limit `[0,1]` doğrulaması UI adapter'ında yapılmalı; NaN/Infinity/negatif değerler bir waveform çizimini bozmak yerine `unavailable` olarak gösterilmelidir. Sayılar user audio'yu temsil ettiğinden sahte random animasyon üretmeye gerek yoktur.

## 25. Tasarım tokenları ile ürün stili ayrımı

**Design'ın sahibi olduğu:** renk, spacing, radius, typography, ikon çizgileri, normal Button/Modal/Switch motion. **Live'ın sahibi olduğu:** merkezi voice panel'in kompozisyonu, status label hizalaması, audio meter geometrisi, konuşma ekranının dar pencere davranışı, model/cihaz listesi ürün mantığı.

Live tarafında `--kw-*` semantic variable'ları üzerinden küçük override yapılabilir. Ancak onlarca magic hex rengi, birebir aynı Button kopyası veya tasarım sisteminde olmayan kurgusal public paket import'ları yoktur. `@imthekaiwen/ui-native` henüz doğrulanmamış olduğundan ürünün web/Electron tarafında kullanılmaz.

### 25.1 UI'da tek tema kaynağı

`theme=system` OS ile birlikte güncellenir. `light`/`dark` tercihi saklanır; model ve audio ayarları ile karışmaz. `motion=balanced` bir tercih olabilir; ancak OS reduced-motion politikası override eder. Density ilk sürümde `comfortable`; advanced diagnostics ekranında `compact` yerleşim değerlendirilebilir ama bütün UI'daki kontrolleri minik ve erişilemez yapmaz.

## 26. Çoklu monitör, DPI ve cihaz değişikliği

Windows'un ses aygıtları Bluetooth bağlantısı, USB çıkarılması ve varsayılan hoparlör değişimi nedeniyle dinamik olabilir. Ayar ekranı cihazların **gerçek sistem adlarını** ve mümkünse yeniden bağlanmaya uygun tanımlayıcıları gösterir; ancak cihaz kimliklerinin kararlı olduğuna körü körüne güvenmez. Yeni bir aygıt takıldığında `selectedDeviceId` doğrulanıp kullanıcıya net seçenek sunulur. Oturum sırasında zorunlu yeniden başlatma gerekiyorsa bunun etkisi anlatılır.

DPI ölçeklendirmesi focus ring'i, tooltip pozisyonunu, modal içeriğini ve meter canvas çözünürlüğünü etkiler. Görsel meter'ın CSS width/height'i ile backing pixel ratio ayrı yönetilir; yüksek DPI'da bulanıklık veya ağır repaint oluşturulmaz. Uygulama focus alıp verirken aktif mikrofona bağlı OS izinleri ve session state rastgele resetlenmez.

## 27. Güvenlik ve güven oluşturan UI kararları

Güvenlik arka planda çalışan tek bir mekanizma değil, kullanıcının kontrolü anlayabilmesidir. Mikrofon açılırken görünür durum, kaydetme açıksa sürekli kayıt simgesi, dış ağ gerekirse açık izin ve model release doğrulaması görünür. ``En iyi deneyim için erişim ver" gibi anlamı belirsiz izin isteme metinleri yerine izin kapsamı kısa açıklanır.

**Önemli sınırlar:**

- Renderer'a `nodeIntegration=true` açılması UX kolaylığı gerekçesiyle kabul edilmez.
- Keyfî `ipcRenderer` kanal erişimi UI bileşenlerine verilmez; typed preload bridge kullanılır.
- Dosya yolları, device ID ve model manifest metni HTML veya shell komutu olarak çalıştırılmaz.
- Log export'u ses, token ve gizli auth bilgisini maskeleyip gerçek formatta üretir.
- Mikrofon kapalı görünürken OS capture açık kalması yüksek öncelikli hata olarak değerlendirilir.
- Agent, model veya kullanıcı metinlerinden gelen tüm açıklamalar untrusted content gibi ele alınır, otomatik sistem komutu değildir.
- Pencere kapanışı audio process ve device resources'ı bırakır; sessiz "arkada dinleme" özelliği yoktur.
- Model kurulum eyleminde imzalı/özeti doğrulanmış artifact tercih edilir; arayüz doğrulama durumunu doğru bildirir.
- "Local-first" sözü ile otomatik network telemetry birbirine karıştırılmaz; izinli indirme ayrı kullanıcı eylemidir.

## 28. İçerik dili, Türkçe metinler ve kullanıcıya hitap

V1 varsayılan dil Türkçe'dir. Metinler teknik ama anlaşılır olur; aşağılayan, çocuklaştıran, aşırı samimi veya uzun açıklama dayatan bir üslup kullanılmaz. "Konuşmayı başlat" ve "Konuşmaya başla" gibi iki eşanlamlı ifade tutarsızlık yaratmasın; bir kopya tablosu hazırlanır.

| Message key (hedef) | Kullanıcıya görünen Türkçe | Gösterim koşulu |
|---|---|---|
| `voice.ready` | `Konuşmaya hazır` | Model ve ses yolu hazır |
| `voice.openingMic` | `Mikrofon açılıyor…` | Capture isteği bekleniyor |
| `voice.listening` | `Dinleniyor` | Capture started kanıtı |
| `voice.endTurn` | `Konuşmayı bitir` | Aktif input turn |
| `voice.processing` | `Yanıt hazırlanıyor…` | Generation başladı ama playback yok |
| `voice.speaking` | `Yanıt çalınıyor` | Gerçek playback started |
| `voice.stopResponse` | `Yanıtı durdur` | Aktif output |
| `voice.cancelResponse` | `Yanıtı iptal et` | Henüz playback olmayan generation |
| `voice.micDenied` | `Mikrofon izni gerekli` | OS izin yok |
| `voice.modelMissing` | `Model seçilmedi` | Aktif geçerli release yok |
| `voice.modelCorrupt` | `Model dosyaları doğrulanamadı` | Hash/manifest başarısız |
| `voice.sidecarFailed` | `Ses motoru durdu` | Runtime process failed |
| `voice.retry` | `Yeniden dene` | İlgili retry eylemi mevcut |
| `voice.close` | `Oturumu kapat` | Aktif session |
| `voice.offline` | `Çevrimdışı kullanım` | Yerel özellikler kullanılabilir |
| `voice.unavailable` | `Bu özellik henüz desteklenmiyor` | Capability false |

Metinler localization kaynağında merkezi tutulur. React bileşenlerinin içine gelişigüzel uzun Türkçe cümleler gömülmez. Uluslararasılaştırma için bütün ürünün ilk günden 10 dile çevrilmesi gerekmiyor; fakat string key ve plural/date formatting mantığı genişlemeye uygun tutulur. `locale="tr"` KaiwenProvider ayarı tüm ürünün otomatik çevrilmesi demek değildir.

## 29. Prototip, Storybook ve tasarım doğrulaması

Tasarım maketi geliştirmeyi hızlandırır ama çalışır sistemin yerine geçmez. İki çalışma hattı vardır: **statik prototip** ve **olaylara bağlı ürün ekranı**. Prototip gerçek ses verisi gerektirmeden placeholder gösterebilir, ancak "Demo / Simülasyon" etiketi taşır. Sonra tasarım aynı bileşenlerin gerçek `LiveViewState` event trace'leriyle sürülmesiyle geçiş yapar.

**Zorunlu Storybook/fixture durumları:**

- Model yok; offline / online.
- Model doğrulanıyor / doğrulama başarısız.
- Mikrofon izni bilinmiyor, reddedildi, verildi.
- Ses cihazı yok, çıkarılmış, meşgul.
- Capture başlatılıyor, başladı, ses var/yok.
- Input turn tamamlandı; model işliyor.
- Output başlıyor; gerçek playback aktif.
- Playback durdu; generation geç yanıtı geldi.
- Model hata verdi; sidecar çöktü; recovery.
- Reduced-motion açık; yüksek kontrast; dar pencere.

Her ekranın klavye odağı, boş durumları ve hata metinleri kontrol edilir. Storybook screenshot'ları yanlış backend akışını kanıtlamaz; yalnız görsel ve erişilebilirlik referansı sağlar.

## 30. Hedef UI test stratejisi

**Birim testleri:** selector/reducer mapping, primary button state, device selection, izin mantığı, telemetry null handling, model uyumluluk metni, çeviri key'leri, primary action idempotency.

**Component testleri:** Button davranışı, focus, loading, disabled, modal, toast, audio meter, reduced-motion. Design kütüphanesinin kendi testini kopyalamak yerine Live kompozisyonunu test et.

**Integration/E2E testleri:** fake sidecar olayları ile session flow; kötü sırada event; late/stale PCM; sidecar crash; device hotplug; model hash mismatch; izin reddi; uzun oturum. Gerçek cihaz testleri ayrıca işaretlenir.

**Görsel regresyon:** Light/dark/system, farklı DPI, dar pencere, uzun Türkçe label, motion off, error states. Screenshot'ın bir renk farkı yakalaması ses motorunun çalıştığını kanıtlamaz.

**Performance:** Renderer JS heap, frame timing, event listener leak, CPU kullanımı ve audio underrun aynı test oturumunda gözlenir. UI hızlı diye output buffer taşmasını yok sayma.

**Mahremiyet:** Açık kayıt izni yokken sesin diske düşmediğini test et; log export'unda kimlik bilgileri/PCM bulunmadığını incele; pencere kapanınca mikrofon OS kaynağının kapandığını doğrula.

### 30.1 Negatif testleri ilk sınıf vatandaş yap

Etkileşim tablosundaki normal akış kadar şu sapmaları da dene: Kullanıcı iki kere hızlı basar, modal açıkken mikrofonu durdurur, Windows izni tam o sırada kaldırılır, çıkış cihazı değiştirilir, sidecar 150 ms sonra restart olur, eski generation `playback.started` event'i gönderir, model 0 frame üretir. UI bu durumlarda **sessiz başarısızlık veya yanlış status** sunamaz.

## 31. V1 kapsam kararları ve tasarım borcu

**V1 içine kesin:** Konuşma ekranı, model/cihaz hazırlığı, açık local-first bilgilendirme, session durumları, manuel kesme, temel model seçimi, ses cihaz testi, hata kurtarma, kolay ayarlar ve diagnostics'a erişim.

**V1 içinde ancak capability ve testle:** native streaming, VAD ile otomatik turn, interruption detector, gerçek output waveform, GPU optimizasyonu.

**V1 sonrasına bırak:** tamamen arka planda wake-word, telefon çağrıları, bulut session sync, çok kullanıcı, zorunlu transcript geçmişi, otomatik uzun süreli kayıt, agent marketplace, ekran paylaşımı, gelişmiş ses karakterleri ve kişisel ses klonlama.

Tasarım borcu kaydı tutulur: Kullanıcı araştırması yapmadan kabul edilen motion süreleri; DPI genişlik seçimleri; hangi audio backend'in seçileceği; model yükleme için tahmini yükleme progress'i; çoklu output device yönetişimi. Bunlar belirsizlik değil, açık araştırma noktalarıdır ve "çalışıyor" diye kapatılmaz.

## 32. Aşamalı uygulama planı — UX0–UX12

| Aşama | İnşa edilecek yüzey | Kabul kanıtı |
|---|---|---|
| `UX0` | Tasarım kararları ve state enum eşlemesi | Bu belge + Architecture sözleşme karşılaştırması |
| `UX1` | Electron/React shell + Design provider | Uygulama açılır, theme/motion ve keyboard çalışır |
| `UX2` | Fake sidecar state-driven konuşma ekranı | Simülasyon etiketi açık; butonlar doğru reducer event'leriyle değişir |
| `UX3` | İzin/cihaz seçme ve hardware test UI | Gerçek device list ve izin reddi senaryosu test edilir |
| `UX4` | Gerçek input capture meter | RMS gerçek veri; sessizlikte/random testinde düz kalır |
| `UX5` | Speech batch output UX | Gerçek checkpoint+codec ile WAV→WAV ve playback kanıtı |
| `UX6` | Session/turn/cancel UI | Stale event/PCM testleri; eski ses geri gelmez |
| `UX7` | Model yönetimi ve Forge release import | Manifest, SHA-256, codec ve rollback testleri |
| `UX8` | Settings, privacy, diagnostics | null metrikler doğru; izin/retention açık |
| `UX9` | Native streaming UX (capability koşullu) | İlk PCM/oynatma olayları gerçek; uygun badge |
| `UX10` | Accessibility/motion/visual QA | Keyboard, NVDA, light/dark/DPI/reduced-motion |
| `UX11` | Windows installer, crash/hotplug robustness | Gerçek Windows cihaz testi, consent ve cleanup |
| `UX12` | Pilot ve measured UX kabulü | Kullanım akışları, benchmark ve açık sorun raporu |

Aşamaların sonunda yalnız screenshot veya kod satırı sayısı değil, **gerçek davranış kanıtı** sunulur. `UX0–UX12` roadmap etiketleridir; repo bugünkü hâliyle bunları tamamlamamıştır. Birinci dikey dilim ancak `UX5` civarında gerçek model/capture/playback üzerinden doğrulanabilir.

## 33. Acceptance kriterleri — ürün seviyesinde

**A. İşlevsel doğruluk:** Kullanıcı bir konuşma turunu başlatıp bitirebilir; model gerçekten ses yanıtı üretiyorsa bunu duyabilir; desteklenmeyen özellik kapalı ve açıklamalıdır. Mikrofon kontrolü OS durumuyla çelişmez.

**B. Denetim:** Kullanıcı çıkış sesini durdurduktan sonra eski PCM yeniden çıkmaz. Oturumu kapatınca kaynağın kapanışı testlidir. Mikrofon izni reddedilince gizli capture devam etmez.

**C. UI güvenilirliği:** Sidecar crash, GPU OOM, model uyumsuzluğu, device loss ve audio underrun anlaşılır eylem sunar. Sonsuz loading, yanlış "hazır" etiketi veya yarım indirmeyi başarılı gösterme yoktur.

**D. Erişilebilirlik:** Ana görev fare dışında klavye ile tamamlanır; durum text ile sunulur; ekran okuyucu anonsu spam değildir; reduced-motion görev başarısını etkilemez.

**E. Performans:** Renderer akıcılığı, capture dropped chunks ve playback underrun ayrı raporlanır; ölçülmeyen TTFA/VRAM iddia edilmez; 2 GB VRAM yalnız gerçek cihazda test geçerse destek etiketi alır.

**F. Güvenlik:** Yerel ses varsayılan olarak dışarı veya kalıcı depoya çıkmaz. Release dosya bütünlüğü kontrol edilir. IPC allowlist, path doğrulama ve desktop sandbox seçimleri güvenlik testlerinden geçer.

**G. Bakım:** UI bileşenleri Design public API'siyle kullanılır; ürün/kit kaynakları kopyalanmaz; code review, testler ve doküman güncellemesi olmadan "tamamlandı" denmez.

## 34. Codex/Agent için görev uygulama ve raporlama protokolü

Her yeni UX görevi başında önce [Live AGENTS](../AGENTS.md), [Architecture](ARCHITECTURE.md), [Speech API](../../kaiwen-speech/docs/API.md) ve ilgili Design component'inin gerçek TS tipini oku. Mevcut olmayan import, hayalî event veya çalışmayan mock SDK üretme. Hedef özellik küçük, doğrulanabilir tek PR'lara bölünmelidir.

**Her PR raporunda:**

1. Hangi kullanıcı problemi çözüldü? Hangi kabul kriteri yürütüldü?
2. Hangi dosyalar ve public contract'lar değişti? Design paket sürümü nedir?
3. Hangi state transition/event işleyicisi eklendi? Gerçek/fake ayrımı nasıl belirtildi?
4. Microphone/device/playback etkisi ve cleanup politikası nedir?
5. Uygulanan `aria-*`, klavye, focus ve reduced-motion kanıtları nelerdir?
6. Hangi unit, component, E2E ve gerçek Windows ses testleri çalıştı? Komut/sonuç?
7. Ses mahremiyeti, log ve model paket güvenliği kontrol edildi mi?
8. Hangi başarısızlık durumları açık kaldı? Gerektiğinde rollback adımı nedir?

**Raporda kullan:** `Implemented`, `Planned`, `Unverified`, `Blocked`; bu kategorileri karıştırma. Ekran görüntüsünü gerçek ses motoru çalışması olarak kanıt gösterme. Test çalıştırılmadıysa bunu açıkça yaz. Eksik model/cihaz nedeniyle uçtan uca doğrulama yapılamadıysa feature tamamlanmış sayılamaz.

## 35. Örnek UI sözleşme testleri — HEDEF

Aşağıdaki TypeScript yalnız davranış önerisi; gerçek Live reducer'ı henüz yoktur. Düşünce şekli frontend durumlarını IPC'den ayrıştırmak, geç event'leri reddetmek ve buton etiketini kullanıcı eylemine bağlamaktır:

```ts
interface SessionEvent {
  sessionId: string;
  epoch: number;
  generationId: string | null;
  type: 'capture.started' | 'generation.started' | 'playback.started';
}

interface ViewModel {
  sessionId: string;
  epoch: number;
  generationId: string | null;
  mode: 'ready' | 'listening' | 'processing' | 'speaking';
}

export function applyEvent(view: ViewModel, event: SessionEvent): ViewModel {
  if (event.sessionId !== view.sessionId || event.epoch !== view.epoch) {
    return view; // stale/foreign session
  }
  if (event.type === 'capture.started') return { ...view, mode: 'listening' };
  if (event.generationId !== view.generationId) return view;
  if (event.type === 'generation.started') return { ...view, mode: 'processing' };
  if (event.type === 'playback.started') return { ...view, mode: 'speaking' };
  return view;
}
```

Bu kod **protokolün tamamı değildir**: `event_id` tekrarları, sıra denetimi, response tamamlanma, timeouts, `stop_playback` ve cancellation gibi olaylar [Architecture](ARCHITECTURE.md) içinde tanımlanan aktör/oturum protokolüne bağlanacaktır. Testler özellikle `generation_id` yeni turda değiştiğinde eski playback event'inin drop edilmesini doğrulamalıdır.

## 36. Kalite test matrisi — UX-01…UX-48

| ID | Senaryo | Beklenen sonuç |
|---|---|---|
| UX-01 | Model yok, ilk açılış | Gerçek model seçme CTA'sı; mikrofon açılmaz |
| UX-02 | Model var, cihaz var | Hazır mesajı, aktif mikrofon değil |
| UX-03 | Mikrofon izni unknown | Açık izin akışı; sahte listening yok |
| UX-04 | OS mikrofon izni denied | Açıklamalı error, cihaz açılma iddiası yok |
| UX-05 | İzin verildi, cihaz açılamadı | Hazır yerine cihaz hatası |
| UX-06 | Capture started event | `Dinleniyor` ve gerçek RMS |
| UX-07 | Capture istek süresi doldu | Retry, timeout ve açık durum |
| UX-08 | 0 PCM / sessizlik | Yapay meter hareketi yok |
| UX-09 | RMS NaN / Infinity | Meter safe fallback, UI crash yok |
| UX-10 | Mikrofon unplug | Cihaz kaybı ve seçim ekranı |
| UX-11 | Cihaz kullanımda | Açıklama, yeniden deneme |
| UX-12 | Input format uygunsuz | Doğrulanmış hata veya desteklenen dönüşüm |
| UX-13 | Output cihazı yok | Ses oynuyor diye gösterilmez |
| UX-14 | Output muted | Çıkış ayarı ve test yönlendirmesi |
| UX-15 | İlk token, PCM yok | `Yanıt hazırlanıyor` durumu korunur |
| UX-16 | İlk PCM decode edildi, henüz çalmıyor | Ölçümler ayrı; yanlış konuşuyor durumu yok |
| UX-17 | Playback started | `Yanıt çalınıyor` gösterilir |
| UX-18 | Playback completed | `Hazır` ve kaynak boşalma |
| UX-19 | Response empty EOS | Ses üretilmedi mesajı |
| UX-20 | Durdur hemen, IPC gecikmeli | Audio hemen kesilir, control ack sonradan |
| UX-21 | Cancel sonrası eski PCM gelir | İki aşamada drop, hoparlörden duyulmaz |
| UX-22 | Yanlış session epoch | UI reducer event'i reddeder |
| UX-23 | Yanlış generation ID | Stale playback started reddedilir |
| UX-24 | İki hızlı buton aktivasyonu | Çift capture/turn oluşturulmaz |
| UX-25 | Sidecar crash | Kalıcı inline error, bounded restart |
| UX-26 | Restart sonrası eski event | UI state geriye dönmez |
| UX-27 | Model hash mismatch | Import/activate bloke edilir |
| UX-28 | Codec uyuşmazlığı | Uyumlu açıklama ve eski sürüme dönüş |
| UX-29 | OOM | Teknik olmayan başlık + gerçek seçenek |
| UX-30 | Model yokken offline | Yalnız yerel import akışı |
| UX-31 | Download yarım kaldı | Tamamlandı iddiası yok; resume/retry |
| UX-32 | İndirme izin gerektiriyor | Ağ kullanımı açık belirtilir |
| UX-33 | Temayı değiştir | Light/dark/system tutarlı |
| UX-34 | Motion off | İşlevsel durum görseli kalır |
| UX-35 | OS reduced-motion | Expressive override etmez |
| UX-36 | Klavye ile tam konuşma turu | Focus ve Space/Enter semantiği geçer |
| UX-37 | Ekran okuyucu | Durum anonsu anlaşılır; meter spam yok |
| UX-38 | 200% zoom | Ana eylem kesilmez |
| UX-39 | 1366×768 laptop | Ana eylem ve hata görünür |
| UX-40 | 150% DPI | Layout, canvas ve modal doğru |
| UX-41 | Uzun Türkçe hata | Yatay taşma/focus kaybı yok |
| UX-42 | Gizlilik varsayılanları | Otomatik kayıt/yükleme yok |
| UX-43 | İzinli session kaydı kapat | Kalıcı record durur, state açık |
| UX-44 | Log export | Audio/token/secrets yok |
| UX-45 | Model değiştir, aktif görüşme | Açık onay, güvenli session kapanışı |
| UX-46 | 30 dakikalık kullanım | UI event listener/heap sızıntısı yok |
| UX-47 | Playback underrun | Ölçüldüyse uyarı; sahte kesintisiz ses iddiası yok |
| UX-48 | Windows app kapanışı | Capture/playback kapatılır; arka planda dinleme yok |

**Test eşiği:** Bunlar test planıdır, koşulmuş test değildir. Her biri fixture ve uygun olgularda gerçek fiziksel cihaz kaydıyla `pass/fail/blocked` olarak raporlanır. `Blocked` ve `not run`, `pass` kabul edilmez. Görsel screenshot bir ses testi değildir.

## 37. Açık kararlar ve karar sahipleri

| Soru | Önerilen başlangıç kararı | Nihai karar için kanıt |
|---|---|---|
| Mikrofon backend'i | Windows üzerinde güvenilir native kütüphane | Audio drop/latency/hotplug testi |
| PCM taşıma | Binary frames, bounded queue | IPC overhead ölçümü |
| Sample rate | Speech release capabilities'e göre cihaz negotiation | Codec ve cihaz uyumluluk testi |
| Push-to-talk | V1'de toggle | Kullanıcı testi, erişilebilirlik ve echo riski |
| Auto VAD turn | Opsiyonel, deneysel | Türkçe gürültü/konuşma testi |
| Waveform çizimi | RMS/peak level meter | Render CPU ve jank testi |
| İlk yükleme | Yerel doğrulanmış release seçimi | Registry manifest doğrulama |
| Agent UI | V1'de yok / opsiyonel | Gerçek adapter ve izin sistemi |
| Transcript geçmişi | Varsayılan yok | Gerçek ASR kaynağı ve gizlilik kararı |
| Oturum kaydı | Varsayılan kapalı | Onay/retention/silme testleri |
| Ana pencere ölçüsü | Laptop odaklı, responsive | Windows DPI ve okunabilirlik testi |
| Açılış animasyonu | Minimal | Cold start ve reduced-motion testleri |

Bu kararlar **tasarım önerisi** niteliğindedir. Kullanıcı testi ve çalışan donanım deneyimiyle değişmeleri normaldir; değişiklik olursa ilgili acceptance testleri de güncellenir. Tasarım estetiği hiçbir zaman mahremiyet, gerçek state veya erişilebilirlik doğruluğunun önüne geçemez.

## 38. Son teslim kontrol listesi

- [ ] Live uygulaması gerçekten Electron/React olarak açılıyor; fake demo açıkça etiketleniyor.
- [ ] Kaiwen Design paketinin gerçek import'ları ve styles.css build ile doğrulandı.
- [ ] Mikrofon durumu OS izni ve capture started onayıyla senkron.
- [ ] Gerçek ses seviyesi dışında sahte audio activity çizilmiyor.
- [ ] Model/codec uyumu doğrulanmadan "Hazır" gösterilmiyor.
- [ ] Konuşma, yanıt hazırlama ve ses oynatma durumları birbirinden ayrı.
- [ ] `stop_playback`, `cancel_generation`, `stop_microphone`, `close_session` ayrı ve testli.
- [ ] Cancel sonrası eski PCM geri dönmüyor; stale event'ler reducer'da reddediliyor.
- [ ] Model import hash/manifest ve rollback UI testli.
- [ ] Mikrofon/hoparlör cihaz kaybı açıkça yönetiliyor.
- [ ] Ana akış fare olmadan klavye ve ekran okuyucuyla tamamlanabiliyor.
- [ ] Reduced-motion altında durum bilgisi kaybolmuyor.
- [ ] Gizlilik varsayılanı ses saklama/yükleme kapalı; kayıt açılışı açık onaylı.
- [ ] Diagnostics ölçülmeyen metrikleri sıfır veya uydurma değer olarak göstermiyor.
- [ ] CPU/GPU baskısı altında UI ve gerçek audio ayrı benchmark'larla raporlanıyor.
- [ ] Gerçek Windows fiziksel cihaz testi ve installer testi yapılmış.
- [ ] Başarısızlık, kısıt ve rollback bilgisi rapora eklenmiş.
- [ ] GitHub'a push veya release yalnız açık talimatla yapılmış.

## 39. Kanonik kaynaklar ve belge bakımı

**Bu repoda:** [README](../README.md), [AGENTS](../AGENTS.md), [ARCHITECTURE](ARCHITECTURE.md). Sıradaki belge `AGENT_INTEGRATION.md` ileride, opsiyonel Agent çağrılarının izin, metin→ses ve araç sonuçlarından konuşmaya dönüş sözleşmesini tanımlayacaktır.

**Kardeş repolarda:** [Speech API](../../kaiwen-speech/docs/API.md), [Speech Streaming](../../kaiwen-speech/docs/STREAMING.md), [Forge Registry](../../kaiwen-forge/docs/MODEL_REGISTRY.md), [Workspace Integration](../../docs/INTEGRATION.md), [Engineering Standards](../../docs/ENGINEERING_STANDARDS.md), [Kaiwen Design GitHub](https://github.com/ImtheKaiwen/kaiwen-design), [Design Language](https://github.com/ImtheKaiwen/kaiwen-design/blob/main/docs/DESIGN_LANGUAGE.md), [Design Component Contract](https://github.com/ImtheKaiwen/kaiwen-design/blob/main/docs/COMPONENT_CONTRACT.md).

**Çelişki çözümü:** Ortak public protokol/codec yükleme için ilgili repo'nun kod ve sürümlü sözleşmesi; kullanıcıya görünen copy/etkileşim için bu dosya; generative coding kuralları için `AGENTS.md`; görsel token/component API için Design paketinin gerçek TypeScript tipleri kaynak kabul edilir. Bu kaynaklar çelişirse varsayımla ilerlemek yerine ADR veya küçük eşzamanlı belge düzeltmesi yap, gerçek kod entegrasyonundan önce contract test ekle.

---

**Son durum:** Bu dosya bir **tasarım ve uygulama şartnamesidir**. Ekran tasarımları, etkileşim kodları, Python sidecar, audio runtime ve gerçek cihaz testleri bu belge yazıldığı için tamamlanmış sayılmaz. Kaiwen Live'ın değeri siyah-beyaz görünümünde değil, **kullanıcının sesinin ne zaman dinlendiğini, yanıtın ne zaman gerçekten üretildiğini ve bütün süreç üzerinde hangi kontrole sahip olduğunu doğru anlatmasındadır**.
