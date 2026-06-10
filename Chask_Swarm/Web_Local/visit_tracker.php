<?php
// Contador de visitas únicas y alertas por Telegram
$visitsFile = __DIR__ . '/visits.txt';
$telegramToken = '8784231970:AAFHcVnTJa0mKDBCalozQkCT7w_Y5twyw8k';
$chatId = '5034994867';
$milestones = [10, 100, 1000, 10000, 100000, 1000000];

// Obtener IP del visitante
$userIp = $_SERVER['REMOTE_ADDR'];
if (isset($_SERVER['HTTP_X_FORWARDED_FOR'])) {
    $userIp = $_SERVER['HTTP_X_FORWARDED_FOR'];
}

// Leer visitas actuales
$visits = [];
if (file_exists($visitsFile)) {
    $lines = file($visitsFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $visits[$line] = true;
    }
}

// Comprobar si es nueva IP
if (!isset($visits[$userIp])) {
    // Registrar nueva IP
    file_put_contents($visitsFile, $userIp . PHP_EOL, FILE_APPEND | LOCK_EX);
    $totalVisits = count($visits) + 1;
    
    // Comprobar hitos
    if (in_array($totalVisits, $milestones)) {
        $message = urlencode("🎉 ¡NUEVO HITO ALCANZADO! 🎉\nLa web www.chask.fun/charm.php acaba de llegar a las {$totalVisits} visitas únicas.");
        $url = "https://api.telegram.org/bot{$telegramToken}/sendMessage?chat_id={$chatId}&text={$message}";
        
        // Enviar notificación a Telegram sin bloquear la carga de la página
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 2); // Timeout corto para no ralentizar la web
        curl_exec($ch);
        curl_close($ch);
    }
}
?>
