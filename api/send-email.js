// Bu dosyanın tam yolu projenizin ana dizininde /api/send-email.js OLMALIDIR

const { Resend } = require('resend');

// Vercel'deki Ortam Değişkenlerinden API anahtarını alıyoruz.
// Bu anahtar, kodun içine doğrudan yazılmadığı için güvenlidir.
const resend = new Resend(process.env.RESEND_API_KEY);

module.exports = async (req, res) => {
  // Sadece POST isteklerini kabul et (güvenlik için)
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed', message: 'Bu endpoint sadece POST isteklerini kabul eder.' });
  }

  try {
    // Gelen isteğin body'sinden (gövdesinden) alıcı, konu ve HTML içeriğini al
    const { to, subject, html } = req.body;

    // Gerekli alanların boş olup olmadığını kontrol et
    if (!to || !subject || !html) {
      return res.status(400).json({ error: 'Missing Parameters', message: 'Alıcı e-posta adresi, konu ve HTML içeriği zorunludur.' });
    }

    // Resend API'sini kullanarak e-posta gönder
    const { data, error } = await resend.emails.send({
      from: 'StudyFlow <onboarding@resend.dev>', // ÖNEMLİ: Ücretsiz Resend planında bu gönderici adresi zorunludur.
                                                  // Kendi doğrulanmış domain adresiniz varsa değiştirebilirsiniz.
      to: [to], // Kime gönderileceği (bir dizi olabilir, biz tek bir alıcı gönderiyoruz)
      subject: subject, // E-postanın konusu
      html: html, // E-postanın HTML içeriği
    });

    if (error) {
      // Resend API'sinden bir hata gelirse
      console.error('Resend API Error:', error);
      return res.status(400).json({ error: error.name, message: error.message });
    }

    // E-posta başarıyla gönderilirse olumlu yanıt dön
    res.status(200).json({ success: true, message: 'E-posta başarıyla gönderildi.', data: data });
  } catch (error) {
    // Beklenmedik bir sunucu hatası olursa
    console.error('Server Error:', error);
    res.status(500).json({ error: 'Internal Server Error', message: error.message });
  }
};