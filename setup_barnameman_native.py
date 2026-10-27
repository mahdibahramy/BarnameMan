import os
import zipfile

FILES = {}

# ۱. تنظیمات Gradle ریشه و پروژه (سازگار با SDKهای جدید اندروید و Gradle 8.7)
FILES["settings.gradle.kts"] = """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "BarnameMan"
include(":app")
"""

FILES["build.gradle.kts"] = """plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.24" apply false
    id("com.google.devtools.ksp") version "1.9.24-1.0.20" apply false
}
"""

FILES["gradle.properties"] = """org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
"""

FILES["app/build.gradle.kts"] = """plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.devtools.ksp")
}

android {
    namespace = "ir.barnameman.nativeapp"
    compileSdk = 35

    defaultConfig {
        applicationId = "ir.barnameman.nativeapp"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"
        vectorDrawables { useSupportLibrary = true }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
        debug {
            applicationIdSuffix = ""
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
    }
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.14"
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.06.00")
    implementation(composeBom)
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.3")
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")

    // Room Database برای ذخیره پایدار آفلاین
    val roomVersion = "2.6.1"
    implementation("androidx.room:room-runtime:$roomVersion")
    implementation("androidx.room:room-ktx:$roomVersion")
    ksp("androidx.room:room-compiler:$roomVersion")
}
"""

# ۲. مانیفست اندروید با مجوزهای دقیق آلارم، اعلان و بازیابی پس از ری‌استارت گوشی
FILES["app/src/main/AndroidManifest.xml"] = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" />
    <uses-permission android:name="android.permission.USE_EXACT_ALARM" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission android:name="android.permission.VIBRATE" />

    <application
        android:allowBackup="true"
        android:label="برنامه من"
        android:supportsRtl="true"
        android:theme="@android:style/Theme.Material.Light.NoActionBar">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <receiver
            android:name=".AlarmReceiver"
            android:exported="false" />

        <receiver
            android:name=".BootReceiver"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
            </intent-filter>
        </receiver>
    </application>
</manifest>
"""

# ۳. موتور تاریخ شمسی (جلالی) و اوقات شرعی ژئوفیزیک تهران در Kotlin
FILES["app/src/main/java/ir/barnameman/nativeapp/CalendarAndPrayerUtils.kt"] = """package ir.barnameman.nativeapp

import java.time.LocalDate
import kotlin.math.*

data class JalaliDateObj(val jy: Int, val jm: Int, val jd: Int)

object PersianCalendarUtils {
    val monthNames = listOf(
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    )
    val weekDayNames = listOf("دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه")

    fun gregorianToJalali(gy: Int, gm: Int, gd: Int): JalaliDateObj {
        val g_d_m = intArrayOf(0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
        val gy2 = if (gm > 2) gy + 1 else gy
        var days = 355666 + (365 * gy) + ((gy2 + 3) / 4) - ((gy2 + 99) / 100) + ((gy2 + 399) / 400) + gd + g_d_m[gm - 1]
        var jy = -1595 + (33 * (days / 12053))
        days %= 12053
        jy += 4 * (days / 1461)
        days %= 1461
        if (days > 365) {
            jy += (days - 1) / 365
            days = (days - 1) % 365
        }
        val jm: Int
        val jd: Int
        if (days < 186) {
            jm = 1 + (days / 31)
            jd = 1 + (days % 31)
        } else {
            jm = 7 + ((days - 186) / 30)
            jd = 1 + ((days - 186) % 30)
        }
        return JalaliDateObj(jy, jm, jd)
    }

    fun jalaliToGregorian(jyInput: Int, jm: Int, jd: Int): LocalDate {
        val jy = jyInput + 1595
        var days = -355668 + (365 * jy) + ((jy / 33) * 8) + (((jy % 33) + 3) / 4) + jd + if (jm < 7) (jm - 1) * 31 else ((jm - 7) * 30) + 186
        var gy = 400 * (days / 146097)
        days %= 146097
        if (days > 36524) {
            gy += 100 * (--days / 36524)
            days %= 36524
            if (days >= 365) days++
        }
        gy += 4 * (days / 1461)
        days %= 1461
        if (days > 365) {
            gy += (days - 1) / 365
            days = (days - 1) % 365
        }
        var gd = days + 1
        val isLeap = (gy % 4 == 0 && gy % 100 != 0) || (gy % 400 == 0)
        val sal_a = intArrayOf(0, 31, if (isLeap) 29 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
        var gm = 0
        while (gm < 13 && gd > sal_a[gm]) {
            gd -= sal_a[gm]
            gm++
        }
        return LocalDate.of(gy, gm, gd)
    }

    fun formatFullShamsi(isoDate: String, persianDigits: Boolean = true): String {
        val ld = LocalDate.parse(isoDate)
        val j = gregorianToJalali(ld.year, ld.monthValue, ld.dayOfMonth)
        val wName = weekDayNames[ld.dayOfWeek.value - 1]
        val raw = "$wName ${j.jd} ${monthNames[j.jm - 1]} ${j.jy}"
        return if (persianDigits) toPersianDigits(raw) else raw
    }

    fun isoToSlashJalali(isoDate: String): String {
        val ld = LocalDate.parse(isoDate)
        val j = gregorianToJalali(ld.year, ld.monthValue, ld.dayOfMonth)
        return "%04d/%02d/%02d".format(j.jy, j.jm, j.jd)
    }

    fun toPersianDigits(input: String): String {
        val pDigits = charArrayOf('۰','۱','۲','۳','۴','۵','۶','۷','۸','۹')
        val sb = StringBuilder()
        for (ch in input) {
            if (ch in '0'..'9') sb.append(pDigits[ch - '0']) else sb.append(ch)
        }
        return sb.toString()
    }

    fun minToTimeStr(minTotal: Int, persianDigits: Boolean = true): String {
        val norm = ((minTotal % 1440) + 1440) % 1440
        val h = norm / 60
        val m = norm % 60
        val str = "%02d:%02d".format(h, m)
        return if (persianDigits) toPersianDigits(str) else str
    }
}

data class CityCoord(val key: String, val nameFa: String, val lat: Double, val lng: Double)
data class DailyPrayerTimes(val fajr: Int, val sunrise: Int, val dhuhr: Int, val maghrib: Int, val isha: Int)

object PrayerCalculator {
    val cities = listOf(
        CityCoord("tehran", "تهران", 35.6892, 51.3890),
        CityCoord("isfahan", "اصفهان", 32.6546, 51.6680),
        CityCoord("qom", "قم", 34.6416, 50.8746),
        CityCoord("sari", "ساری", 36.5633, 53.0601),
        CityCoord("mashhad", "مشهد", 36.2605, 59.6168),
        CityCoord("shiraz", "شیراز", 29.5918, 52.5837),
        CityCoord("tabriz", "تبریز", 38.0962, 46.2738)
    )

    fun calculate(isoDate: String, cityKey: String): DailyPrayerTimes {
        val city = cities.find { it.key == cityKey } ?: cities.first()
        val ld = LocalDate.parse(isoDate)
        val dayOfYear = ld.dayOfYear
        val rad = Math.PI / 180.0
        val deg = 180.0 / Math.PI

        val gamma = (2.0 * Math.PI / 365.0) * (dayOfYear - 1 + 0.5)
        val eqTime = 229.18 * (0.000075 + 0.001868 * cos(gamma) - 0.032077 * sin(gamma)
                - 0.014615 * cos(2 * gamma) - 0.040849 * sin(2 * gamma))
        val decl = (0.006918 - 0.399912 * cos(gamma) + 0.070257 * sin(gamma)
                - 0.006758 * cos(2 * gamma) + 0.000907 * sin(2 * gamma)
                - 0.002697 * cos(3 * gamma) + 0.00148 * sin(3 * gamma))

        val tz = 3.5 // ساعت رسمی ایران
        val dhuhrMin = 720.0 - (4.0 * city.lng) - eqTime + (tz * 60.0)

        fun haMinutes(angleDeg: Double): Double {
            val latR = city.lat * rad
            val cosHA = (cos((90.0 + angleDeg) * rad) - sin(latR) * sin(decl)) / (cos(latR) * cos(decl))
            val clamped = cosHA.coerceIn(-1.0, 1.0)
            return acos(clamped) * deg * 4.0
        }

        // استاندارد مؤسسه ژئوفیزیک دانشگاه تهران (فجر ۱۷.۷ و مغرب ۴.۵ درجه)
        val fajr = (dhuhrMin - haMinutes(17.7)).roundToInt()
        val sunrise = (dhuhrMin - haMinutes(0.833)).roundToInt()
        val dhuhr = dhuhrMin.roundToInt()
        val maghrib = (dhuhrMin + haMinutes(4.5)).roundToInt()
        val isha = (dhuhrMin + haMinutes(14.0)).roundToInt()

        return DailyPrayerTimes(fajr, sunrise, dhuhr, maghrib, isha)
    }
}
"""

# ۴. موجودیت‌های پایگاه داده Room (فعالیت‌ها، نمازها و تنظیمات)
FILES["app/src/main/java/ir/barnameman/nativeapp/AppDatabase.kt"] = """package ir.barnameman.nativeapp

import android.content.Context
import androidx.room.*

@Entity(tableName = "activities")
data class ActivityEntity(
    @PrimaryKey val id: String,
    val title: String,
    val type: String, // "task", "event", "unscheduled", "prayer_override"
    val category: String,
    val isoDate: String, // YYYY-MM-DD
    val startMin: Int,   // دقیقه از شروع شبانه‌روز (0 تا 1440)
    val endMin: Int,
    val prepMin: Int,    // زمان آماده‌شدن به دقیقه
    val travelMin: Int,  // زمان حرکت به دقیقه (بنفش)
    val colorHex: Long,
    val repeatMode: String, // "none", "daily", "weekly"
    val repeatDaysCsv: String, // مثلا "6,1" برای شنبه و دوشنبه
    val remindBeforeTravelMin: Int,
    val priority: String,
    val notes: String,
    val isDone: Boolean
)

@Dao
interface ActivityDao {
    @Query("SELECT * FROM activities")
    suspend fun getAll(): List<ActivityEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(item: ActivityEntity)

    @Delete
    suspend fun delete(item: ActivityEntity)

    @Query("DELETE FROM activities")
    suspend fun clearAll()
}

@Database(entities = [ActivityEntity::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun activityDao(): ActivityDao

    companion object {
        @Volatile private var INSTANCE: AppDatabase? = null
        fun get(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "barname_man_native.db"
                ).build().also { INSTANCE = it }
            }
        }
    }
}
"""

# ۵. مدیریت آلارم‌ها و اعلان‌های واقعی اندروید (AlarmManager + BroadcastReceiver)
FILES["app/src/main/java/ir/barnameman/nativeapp/AlarmSystem.kt"] = """package ir.barnameman.nativeapp

import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.media.RingtoneManager
import android.os.Build
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.ZoneId

class AlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val title = intent.getStringExtra("title") ?: "یادآوری برنامه من"
        val message = intent.getStringExtra("message") ?: "زمان فعالیت فرا رسیده است"
        val notifId = intent.getIntExtra("notifId", 1001)

        val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channelId = "barnameman_alerts"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "اعلان‌های برنامه من",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                enableVibration(true)
                setSound(RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION), null)
            }
            nm.createNotificationChannel(channel)
        }

        val notif = NotificationCompat.Builder(context, channelId)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle(title)
            .setContentText(message)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()

        nm.notify(notifId, notif)
    }
}

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            CoroutineScope(Dispatchers.IO).launch {
                val all = AppDatabase.get(context).activityDao().getAll()
                AlarmScheduler.rescheduleAllTodayAlarms(context, all)
            }
        }
    }
}

object AlarmScheduler {
    fun rescheduleAllTodayAlarms(context: Context, list: List<ActivityEntity>) {
        val todayStr = LocalDate.now().toString()
        val am = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager

        for (act in list) {
            if (act.type == "unscheduled" || act.isDone || act.isoDate != todayStr) continue

            // ۱. هشدار پیش از حرکت (در صورت وجود زمان حرکت)
            if (act.travelMin > 0) {
                val travelStartMin = act.startMin - act.travelMin
                val alertMin = (travelStartMin - act.remindBeforeTravelMin).coerceAtLeast(0)
                scheduleSingle(
                    context, am,
                    (act.id.hashCode() and 0xfffffff) + 1,
                    alertMin,
                    "هشدار حرکت: ${act.title}",
                    "${act.remindBeforeTravelMin} دقیقه دیگر زمان حرکت شماست."
                )
            }

            // ۲. هشدار شروع فعالیت اصلی
            scheduleSingle(
                context, am,
                (act.id.hashCode() and 0xfffffff) + 2,
                act.startMin,
                "شروع برنامه: ${act.title}",
                "هم‌اکنون زمان شروع «${act.title}» است."
            )
        }
    }

    private fun scheduleSingle(
        context: Context,
        am: AlarmManager,
        reqCode: Int,
        minuteOfDay: Int,
        title: String,
        msg: String
    ) {
        val now = LocalDateTime.now()
        val h = (minuteOfDay / 60).coerceIn(0, 23)
        val m = (minuteOfDay % 60).coerceIn(0, 59)
        val target = LocalDateTime.of(LocalDate.now(), LocalTime.of(h, m))
        if (target.isBefore(now)) return

        val triggerMillis = target.atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
        val intent = Intent(context, AlarmReceiver::class.java).apply {
            putExtra("title", title)
            putExtra("message", msg)
            putExtra("notifId", reqCode)
        }
        val pi = PendingIntent.getBroadcast(
            context, reqCode, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        try {
            am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerMillis, pi)
        } catch (_: SecurityException) {}
    }
}
"""

# ۶. رابط کاربری کامل و بومی Jetpack Compose (تایم‌لاین واقعی، هفته، ماه شمسی، بدون زمان، تنظیمات و تداخل)
FILES["app/src/main/java/ir/barnameman/nativeapp/MainActivity.kt"] = """package ir.barnameman.nativeapp

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.time.LocalDate
import java.time.LocalTime
import kotlin.math.roundToInt

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
                BarnameManApp()
            }
        }
    }
}

enum class MainTab(val title: String) {
    TODAY("امروز"),
    WEEK("هفته"),
    MONTH("ماه"),
    UNSCHEDULED("بدون زمان")
}

data class ConflictState(
    val movingItem: ActivityEntity,
    val newStartMin: Int,
    val newEndMin: Int,
    val conflictingTitles: String
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BarnameManApp() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val dao = remember { AppDatabase.get(context).activityDao() }

    // تنظیمات برنامه
    var isDarkTheme by remember { mutableStateOf(false) }
    var selectedCity by remember { mutableStateOf("tehran") }
    var persianNums by remember { mutableStateOf(true) }
    var fajrOffsetMin by remember { mutableStateOf(20) }
    var defaultPrayerDur by remember { mutableStateOf(15) }

    // وضعیت صفحات و زوم تایم‌لاین (۰: ساعتی، ۱: ۱۰دقیقه‌ای، ۲: ۵دقیقه‌ای)
    var currentTab by remember { mutableStateOf(MainTab.TODAY) }
    var selectedIsoDate by remember { mutableStateOf(LocalDate.now().toString()) }
    var zoomLevel by remember { mutableStateOf(0) }
    var showSettingsDrawer by remember { mutableStateOf(false) }

    // داده‌ها
    var allActivities by remember { mutableStateOf(listOf<ActivityEntity>()) }
    var editingActivity by remember { mutableStateOf<ActivityEntity?>(null) }
    var showEditModal by remember { mutableStateOf(false) }
    var forceUnscheduledModal by remember { mutableStateOf(false) }
    var conflictState by remember { mutableStateOf<ConflictState?>(null) }

    // زمان فعلی برای خط قرمز تایم‌لاین
    var nowMinuteOfDay by remember {
        mutableStateOf(LocalTime.now().hour * 60 + LocalTime.now().minute)
    }

    LaunchedEffect(Unit) {
        while (true) {
            nowMinuteOfDay = LocalTime.now().hour * 60 + LocalTime.now().minute
            delay(30_000)
        }
    }

    fun reloadData() {
        scope.launch {
            val loaded = dao.getAll()
            allActivities = loaded
            AlarmScheduler.rescheduleAllTodayAlarms(context, loaded)
        }
    }

    LaunchedEffect(Unit) { reloadData() }

    // درخواست مجوز اعلان در اندروید ۱۳ به بالا
    val notifPermLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) {}
    LaunchedEffect(Unit) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                notifPermLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }

    // پشتیبان‌گیری و بازیابی JSON با انتخابگر فایل استاندارد اندروید
    val exportLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/json")
    ) { uri ->
        if (uri != null) {
            scope.launch {
                val root = JSONObject()
                root.put("app", "برنامه من")
                val arr = JSONArray()
                for (a in allActivities) {
                    val o = JSONObject().apply {
                        put("id", a.id)
                        put("title", a.title)
                        put("type", a.type)
                        put("category", a.category)
                        put("isoDate", a.isoDate)
                        put("startMin", a.startMin)
                        put("endMin", a.endMin)
                        put("prepMin", a.prepMin)
                        put("travelMin", a.travelMin)
                        put("colorHex", a.colorHex)
                        put("repeatMode", a.repeatMode)
                        put("repeatDaysCsv", a.repeatDaysCsv)
                        put("remindBeforeTravelMin", a.remindBeforeTravelMin)
                        put("priority", a.priority)
                        put("notes", a.notes)
                        put("isDone", a.isDone)
                    }
                    arr.put(o)
                }
                root.put("activities", arr)
                context.contentResolver.openOutputStream(uri)?.use { out ->
                    out.write(root.toString(2).toByteArray(Charsets.UTF_8))
                }
                Toast.makeText(context, "فایل پشتیبان با موفقیت ذخیره شد", Toast.LENGTH_SHORT).show()
            }
        }
    }

    val importLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            scope.launch {
                try {
                    val content = context.contentResolver.openInputStream(uri)?.use { inp ->
                        BufferedReader(InputStreamReader(inp)).readText()
                    } ?: ""
                    val obj = JSONObject(content)
                    if (obj.optString("app") != "برنامه من") {
                        Toast.makeText(context, "فایل پشتیبان معتبر نیست", Toast.LENGTH_LONG).show()
                        return@launch
                    }
                    val arr = obj.getJSONArray("activities")
                    dao.clearAll()
                    for (i in 0 until arr.length()) {
                        val o = arr.getJSONObject(i)
                        dao.upsert(
                            ActivityEntity(
                                id = o.getString("id"),
                                title = o.getString("title"),
                                type = o.getString("type"),
                                category = o.optString("category", "عمومی"),
                                isoDate = o.getString("isoDate"),
                                startMin = o.getInt("startMin"),
                                endMin = o.getInt("endMin"),
                                prepMin = o.optInt("prepMin", 0),
                                travelMin = o.optInt("travelMin", 0),
                                colorHex = o.optLong("colorHex", 0xFF0F766E),
                                repeatMode = o.optString("repeatMode", "none"),
                                repeatDaysCsv = o.optString("repeatDaysCsv", ""),
                                remindBeforeTravelMin = o.optInt("remindBeforeTravelMin", 10),
                                priority = o.optString("priority", "med"),
                                notes = o.optString("notes", ""),
                                isDone = o.optBoolean("isDone", false)
                            )
                        )
                    }
                    reloadData()
                    Toast.makeText(context, "اطلاعات با موفقیت بازیابی شد", Toast.LENGTH_SHORT).show()
                } catch (e: Exception) {
                    Toast.makeText(context, "خطا در بازیابی فایل پشتیبان", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    // استخراج برنامه‌های روز انتخابی به همراه ۵ بلوک مستقل نماز
    fun buildDaySchedule(isoDate: String): List<ActivityEntity> {
        val ld = LocalDate.parse(isoDate)
        val dow = ld.dayOfWeek.value % 7 // 6 = شنبه
        val result = mutableListOf<ActivityEntity>()

        for (a in allActivities) {
            if (a.type == "unscheduled" || a.type == "prayer_override") continue
            val match = when (a.repeatMode) {
                "daily" -> a.isoDate <= isoDate
                "weekly" -> a.isoDate <= isoDate && a.repeatDaysCsv.split(",").contains(dow.toString())
                else -> a.isoDate == isoDate
            }
            if (match) result.add(a)
        }

        // افزودن ۵ بلوک مستقل نماز (صبح، ظهر، عصر، مغرب، عشا)
        val pt = PrayerCalculator.calculate(isoDate, selectedCity)
        val prayers = listOf(
            Triple("fajr", "نماز صبح", pt.fajr + fajrOffsetMin),
            Triple("dhuhr", "نماز ظهر", pt.dhuhr),
            Triple("asr", "نماز عصر", pt.dhuhr + defaultPrayerDur),
            Triple("maghrib", "نماز مغرب", pt.maghrib),
            Triple("isha", "نماز عشا", pt.isha)
        )
        for ((key, title, defStart) in prayers) {
            val overrideId = "prayer_${isoDate}_$key"
            val saved = allActivities.find { it.id == overrideId }
            if (saved != null) {
                result.add(saved)
            } else {
                result.add(
                    ActivityEntity(
                        id = overrideId,
                        title = title,
                        type = "prayer_override",
                        category = "عبادت",
                        isoDate = isoDate,
                        startMin = defStart,
                        endMin = defStart + defaultPrayerDur,
                        prepMin = 0,
                        travelMin = 0,
                        colorHex = 0xFF059669,
                        repeatMode = "none",
                        repeatDaysCsv = "",
                        remindBeforeTravelMin = 0,
                        priority = "med",
                        notes = "بلوک مستقل نماز",
                        isDone = false
                    )
                )
            }
        }
        return result.sortedBy { it.startMin - it.prepMin - it.travelMin }
    }

    val colorScheme = if (isDarkTheme) darkColorScheme(
        primary = Color(0xFF14B8A6),
        background = Color(0xFF0F172A),
        surface = Color(0xFF1E293B)
    ) else lightColorScheme(
        primary = Color(0xFF0F766E),
        background = Color(0xFFF8FAFC),
        surface = Color(0xFFFFFFFF)
    )

    MaterialTheme(colorScheme = colorScheme) {
        Box(modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
            Scaffold(
                topBar = {
                    TopAppBar(
                        title = {
                            Column {
                                Text("برنامه من", fontWeight = FontWeight.ExtraBold, fontSize = 19.sp)
                                Text(
                                    PersianCalendarUtils.formatFullShamsi(selectedIsoDate, persianNums),
                                    fontSize = 12.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        },
                        actions = {
                            TextButton(onClick = { selectedIsoDate = LocalDate.now().toString() }) {
                                Text("امروز")
                            }
                            IconButton(onClick = { showSettingsDrawer = true }) {
                                Icon(Icons.Default.Settings, contentDescription = "تنظیمات")
                            }
                        }
                    )
                },
                bottomBar = {
                    NavigationBar {
                        MainTab.values().forEach { tab ->
                            NavigationBarItem(
                                selected = currentTab == tab,
                                onClick = { currentTab = tab },
                                icon = {
                                    val ic = when (tab) {
                                        MainTab.TODAY -> Icons.Default.Schedule
                                        MainTab.WEEK -> Icons.Default.ViewWeek
                                        MainTab.MONTH -> Icons.Default.CalendarMonth
                                        MainTab.UNSCHEDULED -> Icons.Default.Inbox
                                    }
                                    Icon(ic, contentDescription = tab.title)
                                },
                                label = { Text(tab.title) }
                            )
                        }
                    }
                },
                floatingActionButton = {
                    FloatingActionButton(
                        onClick = {
                            editingActivity = null
                            forceUnscheduledModal = (currentTab == MainTab.UNSCHEDULED)
                            showEditModal = true
                        },
                        containerColor = MaterialTheme.colorScheme.primary
                    ) {
                        Icon(Icons.Default.Add, contentDescription = "افزودن", tint = Color.White)
                    }
                }
            ) { innerPadding ->
                Box(modifier = Modifier.padding(innerPadding).fillMaxSize()) {
                    when (currentTab) {
                        MainTab.TODAY -> TodayTimelineScreen(
                            isoDate = selectedIsoDate,
                            onChangeDate = { selectedIsoDate = it },
                            zoomLevel = zoomLevel,
                            onChangeZoom = { zoomLevel = it },
                            activities = buildDaySchedule(selectedIsoDate),
                            prayerTimes = PrayerCalculator.calculate(selectedIsoDate, selectedCity),
                            cityName = PrayerCalculator.cities.find { it.key == selectedCity }?.nameFa ?: "تهران",
                            nowMin = nowMinuteOfDay,
                            persianNums = persianNums,
                            onEditClick = { item ->
                                editingActivity = item
                                forceUnscheduledModal = false
                                showEditModal = true
                            },
                            onToggleDone = { item ->
                                scope.launch {
                                    dao.upsert(item.copy(isDone = !item.isDone))
                                    reloadData()
                                }
                            },
                            onDragFinished = { item, newStartMin ->
                                val dur = item.endMin - item.startMin
                                val newEndMin = newStartMin + dur
                                val newEffStart = newStartMin - item.prepMin - item.travelMin
                                val others = buildDaySchedule(selectedIsoDate).filter { it.id != item.id }
                                val overlaps = others.filter { o ->
                                    val oEff = o.startMin - o.prepMin - o.travelMin
                                    newEffStart < o.endMin && newEndMin > oEff
                                }
                                if (overlaps.isEmpty()) {
                                    scope.launch {
                                        dao.upsert(item.copy(startMin = newStartMin, endMin = newEndMin))
                                        reloadData()
                                    }
                                } else {
                                    conflictState = ConflictState(
                                        movingItem = item,
                                        newStartMin = newStartMin,
                                        newEndMin = newEndMin,
                                        conflictingTitles = overlaps.joinToString("، ") { "«${it.title}»" }
                                    )
                                }
                            }
                        )

                        MainTab.WEEK -> WeekViewScreen(
                            selectedIsoDate = selectedIsoDate,
                            persianNums = persianNums,
                            getDayList = { buildDaySchedule(it) },
                            onSelectDateToTimeline = {
                                selectedIsoDate = it
                                currentTab = MainTab.TODAY
                            }
                        )

                        MainTab.MONTH -> MonthShamsiScreen(
                            selectedIsoDate = selectedIsoDate,
                            persianNums = persianNums,
                            getDayCount = { iso -> buildDaySchedule(iso).count { it.type != "prayer_override" } },
                            onSelectDay = {
                                selectedIsoDate = it
                                currentTab = MainTab.TODAY
                            }
                        )

                        MainTab.UNSCHEDULED -> UnscheduledScreen(
                            items = allActivities.filter { it.type == "unscheduled" },
                            onScheduleItem = { item ->
                                editingActivity = item.copy(type = "task", isoDate = selectedIsoDate)
                                forceUnscheduledModal = false
                                showEditModal = true
                            },
                            onToggleDone = { item ->
                                scope.launch {
                                    dao.upsert(item.copy(isDone = !item.isDone))
                                    reloadData()
                                }
                            },
                            onDelete = { item ->
                                scope.launch {
                                    dao.delete(item)
                                    reloadData()
                                }
                            }
                        )
                    }
                }
            }

            // پنل تنظیمات راست‌به‌چپ روی صفحه فعلی بدون ریست شدن وضعیت اسکرول
            if (showSettingsDrawer) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(alpha = 0.5f))
                        .clickable { showSettingsDrawer = false }
                ) {
                    Surface(
                        modifier = Modifier
                            .fillMaxHeight()
                            .width(310.dp)
                            .align(Alignment.CenterStart)
                            .clickable(enabled = false) {},
                        color = MaterialTheme.colorScheme.surface,
                        tonalElevation = 8.dp
                    ) {
                        Column(
                            modifier = Modifier
                                .padding(16.dp)
                                .verticalScroll(rememberScrollState()),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text("تنظیمات «برنامه من»", fontWeight = FontWeight.Bold, fontSize = 17.sp)
                                IconButton(onClick = { showSettingsDrawer = false }) {
                                    Icon(Icons.Default.Close, contentDescription = "بستن")
                                }
                            }
                            HorizontalDivider()
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text("حالت تاریک (شب)")
                                Switch(checked = isDarkTheme, onCheckedChange = { isDarkTheme = it })
                            }
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text("نمایش اعداد فارسی")
                                Switch(checked = persianNums, onCheckedChange = { persianNums = it })
                            }
                            HorizontalDivider()
                            Text("شهر اوقات شرعی (ژئوفیزیک تهران):", fontWeight = FontWeight.Bold)
                            PrayerCalculator.cities.forEach { c ->
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clickable { selectedCity = c.key }
                                        .padding(vertical = 4.dp)
                                ) {
                                    RadioButton(selected = selectedCity == c.key, onClick = { selectedCity = c.key })
                                    Text(c.nameFa)
                                }
                            }
                            HorizontalDivider()
                            Text("پشتیبان‌گیری و بازیابی اطلاعات:", fontWeight = FontWeight.Bold)
                            Button(
                                onClick = { exportLauncher.launch("BarnameMan-Backup-$selectedIsoDate.json") },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text("📤 ذخیره فایل پشتیبان (JSON)")
                            }
                            OutlinedButton(
                                onClick = { importLauncher.launch(arrayOf("application/json", "*/*")) },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text("📥 بازیابی از فایل پشتیبان")
                            }
                        }
                    }
                }
            }

            // مودال افزودن / ویرایش کار و رویداد
            if (showEditModal) {
                ActivityEditDialog(
                    initial = editingActivity,
                    defaultIsoDate = selectedIsoDate,
                    forceUnscheduled = forceUnscheduledModal,
                    onDismiss = { showEditModal = false },
                    onSave = { entity ->
                        scope.launch {
                            dao.upsert(entity)
                            reloadData()
                            showEditModal = false
                        }
                    },
                    onDelete = { entity ->
                        scope.launch {
                            dao.delete(entity)
                            reloadData()
                            showEditModal = false
                        }
                    }
                )
            }

            // مودال تصمیم‌گیری هنگام تداخل زمانی
            conflictState?.let { cf ->
                AlertDialog(
                    onDismissRequest = { conflictState = null },
                    title = { Text("⚠️ تداخل زمانی شناسایی شد", fontWeight = FontWeight.Bold) },
                    text = {
                        Text("جابه‌جایی «${cf.movingItem.title}» (با احتساب آماده‌شدن و حرکت) با برنامهٔ ${cf.conflictingTitles} تداخل دارد. چه کاری انجام شود؟")
                    },
                    confirmButton = {
                        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Button(
                                onClick = {
                                    scope.launch {
                                        dao.upsert(cf.movingItem.copy(startMin = cf.newStartMin, endMin = cf.newEndMin))
                                        var cursorEnd = cf.newEndMin
                                        val dayItems = buildDaySchedule(selectedIsoDate)
                                            .filter { it.id != cf.movingItem.id && (it.startMin - it.prepMin - it.travelMin) >= (cf.newStartMin - cf.movingItem.prepMin - cf.movingItem.travelMin) }
                                        for (next in dayItems) {
                                            val nOffset = next.prepMin + next.travelMin
                                            if (next.startMin - nOffset < cursorEnd) {
                                                val dur = next.endMin - next.startMin
                                                val shiftedStart = cursorEnd + nOffset
                                                val shiftedEnd = shiftedStart + dur
                                                dao.upsert(next.copy(startMin = shiftedStart, endMin = shiftedEnd))
                                                cursorEnd = shiftedEnd
                                            }
                                        }
                                        conflictState = null
                                        reloadData()
                                    }
                                },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text("۱. جابه‌جایی خودکار برنامه‌های بعدی")
                            }
                            OutlinedButton(
                                onClick = { conflictState = null },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text("۲. لغو تغییر و بازگشت")
                            }
                        }
                    }
                )
            }
        }
    }
}

@Composable
fun TodayTimelineScreen(
    isoDate: String,
    onChangeDate: (String) -> Unit,
    zoomLevel: Int,
    onChangeZoom: (Int) -> Unit,
    activities: List<ActivityEntity>,
    prayerTimes: DailyPrayerTimes,
    cityName: String,
    nowMin: Int,
    persianNums: Boolean,
    onEditClick: (ActivityEntity) -> Unit,
    onToggleDone: (ActivityEntity) -> Unit,
    onDragFinished: (ActivityEntity, Int) -> Unit
) {
    // ضریب ارتفاع واقعی به ازای هر دقیقه: زوم ساعتی (1.2dp)، زوم ۱۰دقیقه‌ای (2.5dp)، زوم ۵دقیقه‌ای (4.2dp)
    val dpPerMin = when (zoomLevel) {
        0 -> 1.2f
        1 -> 2.5f
        else -> 4.2f
    }
    val stepMin = when (zoomLevel) {
        0 -> 60
        1 -> 10
        else -> 5
    }
    val zoomLabel = when (zoomLevel) {
        0 -> "نمای ساعتی"
        1 -> "شبکه ۱۰دقیقه‌ای"
        else -> "شبکه ۵دقیقه‌ای"
    }

    Column(modifier = Modifier.fillMaxSize()) {
        // نوار کنترل تاریخ و بزرگ‌نمایی
        Surface(tonalElevation = 2.dp, modifier = Modifier.fillMaxWidth()) {
            Row(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp).fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    OutlinedButton(
                        onClick = { onChangeDate(LocalDate.parse(isoDate).minusDays(1).toString()) },
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp)
                    ) { Text("روز قبل") }
                    Spacer(Modifier.width(6.dp))
                    OutlinedButton(
                        onClick = { onChangeDate(LocalDate.parse(isoDate).plusDays(1).toString()) },
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp)
                    ) { Text("روز بعد") }
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = { onChangeZoom((zoomLevel - 1).coerceAtLeast(0)) }) {
                        Text("➖")
                    }
                    Text(zoomLabel, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    IconButton(onClick = { onChangeZoom((zoomLevel + 1).coerceAtMost(2)) }) {
                        Text("➕")
                    }
                }
            }
        }

        // نوار خلاصه اوقات شرعی
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.surfaceVariant)
                .horizontalScroll(rememberScrollState())
                .padding(horizontal = 12.dp, vertical = 5.dp),
            horizontalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Text("🕌 اوقات شرعی ($cityName):", fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Text("اذان صبح: ${PersianCalendarUtils.minToTimeStr(prayerTimes.fajr, persianNums)}", fontSize = 11.sp)
            Text("طلوع: ${PersianCalendarUtils.minToTimeStr(prayerTimes.sunrise, persianNums)}", fontSize = 11.sp)
            Text("اذان ظهر: ${PersianCalendarUtils.minToTimeStr(prayerTimes.dhuhr, persianNums)}", fontSize = 11.sp)
            Text("اذان مغرب: ${PersianCalendarUtils.minToTimeStr(prayerTimes.maghrib, persianNums)}", fontSize = 11.sp)
        }

        // محور زمانی عمودی واقعی (۱۴۴۰ دقیقه)
        val scrollState = rememberScrollState()
        Box(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(scrollState)
                .padding(bottom = 84.dp)
        ) {
            val totalHeightDp = (1440 * dpPerMin).dp
            Box(modifier = Modifier.fillMaxWidth().height(totalHeightDp)) {

                // ۱. خطوط شبکه و خط‌کش ساعت در سمت راست
                var m = 0
                while (m <= 1440) {
                    val yOffset = (m * dpPerMin).dp
                    val isHour = (m % 60 == 0)
                    Row(
                        modifier = Modifier.fillMaxWidth().offset(y = yOffset),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = PersianCalendarUtils.minToTimeStr(m, persianNums),
                            fontSize = if (isHour) 11.sp else 9.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.width(52.dp).padding(start = 6.dp)
                        )
                        HorizontalDivider(
                            thickness = if (isHour) 1.dp else 0.5.dp,
                            color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = if (isHour) 0.7f else 0.35f)
                        )
                    }
                    m += stepMin
                }

                // ۲. خطوط افقی باریک اذان (متمایز از بلوک‌های نماز)
                val azans = listOf(
                    prayerTimes.fajr to "اذان صبح",
                    prayerTimes.dhuhr to "اذان ظهر",
                    prayerTimes.maghrib to "اذان مغرب"
                )
                for ((azMin, label) in azans) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(start = 52.dp)
                            .offset(y = (azMin * dpPerMin).dp)
                    ) {
                        HorizontalDivider(thickness = 2.dp, color = Color(0xFFE11D48))
                        Surface(
                            color = Color(0xFFE11D48),
                            shape = RoundedCornerShape(4.dp),
                            modifier = Modifier.align(Alignment.CenterEnd).padding(end = 8.dp)
                        ) {
                            Text(
                                text = "$label ${PersianCalendarUtils.minToTimeStr(azMin, persianNums)}",
                                color = Color.White,
                                fontSize = 10.sp,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 1.dp)
                            )
                        }
                    }
                }

                // ۳. خط زمان فعلی
                if (isoDate == LocalDate.now().toString()) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(start = 48.dp)
                            .offset(y = (nowMin * dpPerMin).dp)
                    ) {
                        HorizontalDivider(thickness = 2.dp, color = Color.Red)
                        Box(
                            modifier = Modifier
                                .size(9.dp)
                                .clip(CircleShape)
                                .background(Color.Red)
                                .align(Alignment.CenterStart)
                        )
                    }
                }

                // ۴. بلوک‌های فعالیت به همراه آماده‌شدن و حرکت (بنفش) و Drag & Drop
                for (act in activities) {
                    var dragOffsetMin by remember(act.id, act.startMin) { mutableStateOf(0f) }
                    val effectiveStartMin = (act.startMin + dragOffsetMin.roundToInt()) - act.prepMin - act.travelMin
                    val mainDuration = (act.endMin - act.startMin).coerceAtLeast(10)

                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(start = 56.dp, end = 10.dp)
                            .offset(y = (effectiveStartMin * dpPerMin).dp)
                            .pointerInput(act.id, dpPerMin) {
                                detectVerticalDragGestures(
                                    onDragEnd = {
                                        val deltaRounded = ((dragOffsetMin / 5f).roundToInt()) * 5
                                        if (deltaRounded != 0) {
                                            val newStart = (act.startMin + deltaRounded).coerceIn(
                                                act.prepMin + act.travelMin,
                                                1440 - mainDuration
                                            )
                                            onDragFinished(act, newStart)
                                        }
                                        dragOffsetMin = 0f
                                    },
                                    onVerticalDrag = { change, dragAmount ->
                                        change.consume()
                                        val deltaDp = dragAmount / density
                                        dragOffsetMin += (deltaDp / dpPerMin)
                                    }
                                )
                            }
                    ) {
                        // بلوک آماده‌شدن متصل
                        if (act.prepMin > 0) {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height((act.prepMin * dpPerMin).dp.coerceAtLeast(18.dp))
                                    .clip(RoundedCornerShape(topStart = 8.dp, topEnd = 8.dp))
                                    .background(Color(0xFFD97706))
                                    .padding(horizontal = 8.dp),
                                contentAlignment = Alignment.CenterStart
                            ) {
                                Text(
                                    "🛠 آماده‌شدن (${act.prepMin} دقیقه)",
                                    color = Color.White,
                                    fontSize = 10.sp
                                )
                            }
                        }

                        // بلوک حرکت و رفت‌وآمد (بنفش، مستقیماً قبل از فعالیت اصلی)
                        if (act.travelMin > 0) {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height((act.travelMin * dpPerMin).dp.coerceAtLeast(18.dp))
                                    .background(Color(0xFF7C3AED))
                                    .padding(horizontal = 8.dp),
                                contentAlignment = Alignment.CenterStart
                            ) {
                                Text(
                                    "🟣 حرکت و رفت‌وآمد (${act.travelMin} دقیقه)",
                                    color = Color.White,
                                    fontSize = 10.sp
                                )
                            }
                        }

                        // بلوک اصلی فعالیت
                        val currentStart = act.startMin + ((dragOffsetMin / 5f).roundToInt() * 5)
                        val currentEnd = currentStart + mainDuration
                        Surface(
                            color = Color(act.colorHex).copy(alpha = if (act.isDone) 0.55f else 0.95f),
                            shape = RoundedCornerShape(
                                topStart = if (act.prepMin > 0 || act.travelMin > 0) 0.dp else 8.dp,
                                topEnd = if (act.prepMin > 0 || act.travelMin > 0) 0.dp else 8.dp,
                                bottomStart = 8.dp,
                                bottomEnd = 8.dp
                            ),
                            modifier = Modifier
                                .fillMaxWidth()
                                .height((mainDuration * dpPerMin).dp.coerceAtLeast(28.dp))
                                .clickable { onEditClick(act) }
                        ) {
                            Row(
                                modifier = Modifier.fillMaxSize().padding(horizontal = 10.dp, vertical = 4.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        text = act.title,
                                        color = Color.White,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 13.sp,
                                        textDecoration = if (act.isDone) TextDecoration.LineThrough else TextDecoration.None
                                    )
                                    Text(
                                        text = "${PersianCalendarUtils.minToTimeStr(currentStart, persianNums)} تا ${PersianCalendarUtils.minToTimeStr(currentEnd, persianNums)}",
                                        color = Color.White.copy(alpha = 0.9f),
                                        fontSize = 11.sp
                                    )
                                }
                                Checkbox(
                                    checked = act.isDone,
                                    onCheckedChange = { onToggleDone(act) },
                                    colors = CheckboxDefaults.colors(checkedColor = Color.White, checkmarkColor = Color.Black)
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun WeekViewScreen(
    selectedIsoDate: String,
    persianNums: Boolean,
    getDayList: (String) -> List<ActivityEntity>,
    onSelectDateToTimeline: (String) -> Unit
) {
    val baseDate = LocalDate.parse(selectedIsoDate)
    val diffToSat = (baseDate.dayOfWeek.value + 1) % 7
    val saturday = baseDate.minusDays(diffToSat.toLong())

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Text("برنامهٔ هفتگی (شنبه تا جمعه)", fontWeight = FontWeight.Bold, fontSize = 16.sp)
        for (i in 0..6) {
            val dayIso = saturday.plusDays(i.toLong()).toString()
            val list = getDayList(dayIso)
            Card(
                modifier = Modifier.fillMaxWidth().clickable { onSelectDateToTimeline(dayIso) }
            ) {
                Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(PersianCalendarUtils.formatFullShamsi(dayIso, persianNums), fontWeight = FontWeight.Bold)
                        Text("ورود به تایم‌لاین ◀", fontSize = 12.sp, color = MaterialTheme.colorScheme.primary)
                    }
                    list.forEach { a ->
                        Text(
                            "• ${a.title} (${PersianCalendarUtils.minToTimeStr(a.startMin, persianNums)} - ${PersianCalendarUtils.minToTimeStr(a.endMin, persianNums)})",
                            fontSize = 12.sp
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun MonthShamsiScreen(
    selectedIsoDate: String,
    persianNums: Boolean,
    getDayCount: (String) -> Int,
    onSelectDay: (String) -> Unit
) {
    var currentIso by remember { mutableStateOf(selectedIsoDate) }
    val ld = LocalDate.parse(currentIso)
    val j = PersianCalendarUtils.gregorianToJalali(ld.year, ld.monthValue, ld.dayOfMonth)
    val daysInMonth = if (j.jm <= 6) 31 else if (j.jm <= 11) 30 else 29

    Column(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedButton(onClick = {
                val prevM = if (j.jm == 1) 12 else j.jm - 1
                val prevY = if (j.jm == 1) j.jy - 1 else j.jy
                currentIso = PersianCalendarUtils.jalaliToGregorian(prevY, prevM, 1).toString()
            }) { Text("ماه قبل") }

            Text(
                PersianCalendarUtils.toPersianDigits("${PersianCalendarUtils.monthNames[j.jm - 1]} ${j.jy}"),
                fontWeight = FontWeight.ExtraBold,
                fontSize = 18.sp
            )

            OutlinedButton(onClick = {
                val nextM = if (j.jm == 12) 1 else j.jm + 1
                val nextY = if (j.jm == 12) j.jy + 1 else j.jy
                currentIso = PersianCalendarUtils.jalaliToGregorian(nextY, nextM, 1).toString()
            }) { Text("ماه بعد") }
        }

        // شبکه روزهای ماه شمسی
        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
            for (row in 0..4) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    for (col in 1..7) {
                        val dayNum = row * 7 + col
                        if (dayNum <= daysInMonth) {
                            val gDate = PersianCalendarUtils.jalaliToGregorian(j.jy, j.jm, dayNum).toString()
                            val count = getDayCount(gDate)
                            Surface(
                                tonalElevation = if (count > 0) 4.dp else 1.dp,
                                shape = RoundedCornerShape(8.dp),
                                border = BorderStroke(
                                    1.dp,
                                    if (gDate == LocalDate.now().toString()) MaterialTheme.colorScheme.primary else Color.LightGray
                                ),
                                modifier = Modifier
                                    .weight(1f)
                                    .height(58.dp)
                                    .clickable { onSelectDay(gDate) }
                            ) {
                                Column(
                                    modifier = Modifier.padding(4.dp),
                                    horizontalAlignment = Alignment.CenterHorizontally,
                                    verticalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text(
                                        PersianCalendarUtils.toPersianDigits(dayNum.toString()),
                                        fontWeight = FontWeight.Bold
                                    )
                                    if (count > 0) {
                                        Text(
                                            "${PersianCalendarUtils.toPersianDigits(count.toString())} برنامه",
                                            fontSize = 9.sp,
                                            color = MaterialTheme.colorScheme.primary
                                        )
                                    }
                                }
                            }
                        } else {
                            Spacer(modifier = Modifier.weight(1f))
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun UnscheduledScreen(
    items: List<ActivityEntity>,
    onScheduleItem: (ActivityEntity) -> Unit,
    onToggleDone: (ActivityEntity) -> Unit,
    onDelete: (ActivityEntity) -> Unit
) {
    var query by remember { mutableStateOf("") }
    val filtered = items.filter { query.isBlank() || it.title.contains(query, ignoreCase = true) }

    Column(
        modifier = Modifier.fillMaxSize().padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            label = { Text("جست‌وجو در کارهای بدون زمان...") },
            modifier = Modifier.fillMaxWidth()
        )
        if (filtered.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("هیچ کار بدون زمانی ثبت نشده است.")
            }
        } else {
            Column(
                modifier = Modifier.verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                filtered.forEach { item ->
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Row(
                            modifier = Modifier.padding(12.dp).fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    item.title,
                                    fontWeight = FontWeight.Bold,
                                    textDecoration = if (item.isDone) TextDecoration.LineThrough else TextDecoration.None
                                )
                                Text("دسته: ${item.category} | اولویت: ${item.priority}", fontSize = 12.sp)
                            }
                            Row {
                                TextButton(onClick = { onScheduleItem(item) }) { Text("🕒 زمان‌بندی") }
                                IconButton(onClick = { onToggleDone(item) }) {
                                    Icon(Icons.Default.Check, contentDescription = "انجام")
                                }
                                IconButton(onClick = { onDelete(item) }) {
                                    Icon(Icons.Default.Delete, contentDescription = "حذف")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ActivityEditDialog(
    initial: ActivityEntity?,
    defaultIsoDate: String,
    forceUnscheduled: Boolean,
    onDismiss: () -> Unit,
    onSave: (ActivityEntity) -> Unit,
    onDelete: (ActivityEntity) -> Unit
) {
    var title by remember { mutableStateOf(initial?.title ?: "") }
    var type by remember {
        mutableStateOf(if (forceUnscheduled) "unscheduled" else (initial?.type ?: "task"))
    }
    var category by remember { mutableStateOf(initial?.category ?: "عمومی") }
    var startHour by remember { mutableStateOf(((initial?.startMin ?: 540) / 60).toString()) }
    var startMinute by remember { mutableStateOf(((initial?.startMin ?: 540) % 60).toString()) }
    var durationMin by remember {
        mutableStateOf(((initial?.endMin ?: 600) - (initial?.startMin ?: 540)).toString())
    }
    var prepMin by remember { mutableStateOf((initial?.prepMin ?: 0).toString()) }
    var travelMin by remember { mutableStateOf((initial?.travelMin ?: 0).toString()) }
    var repeatMode by remember { mutableStateOf(initial?.repeatMode ?: "none") }
    var notes by remember { mutableStateOf(initial?.notes ?: "") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (initial == null) "افزودن فعالیت جدید" else "ویرایش فعالیت") },
        text = {
            Column(
                modifier = Modifier.verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedTextField(
                    value = title,
                    onValueChange = { title = it },
                    label = { Text("عنوان فعالیت") },
                    modifier = Modifier.fillMaxWidth()
                )
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    FilterChip(
                        selected = type == "task",
                        onClick = { type = "task" },
                        label = { Text("کار") }
                    )
                    FilterChip(
                        selected = type == "event",
                        onClick = { type = "event" },
                        label = { Text("رویداد") }
                    )
                    FilterChip(
                        selected = type == "unscheduled",
                        onClick = { type = "unscheduled" },
                        label = { Text("بدون ساعت") }
                    )
                }

                if (type != "unscheduled") {
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        OutlinedTextField(
                            value = startHour,
                            onValueChange = { startHour = it },
                            label = { Text("ساعت شروع") },
                            modifier = Modifier.weight(1f)
                        )
                        OutlinedTextField(
                            value = startMinute,
                            onValueChange = { startMinute = it },
                            label = { Text("دقیقه شروع") },
                            modifier = Modifier.weight(1f)
                        )
                        OutlinedTextField(
                            value = durationMin,
                            onValueChange = { durationMin = it },
                            label = { Text("مدت (دقیقه)") },
                            modifier = Modifier.weight(1f)
                        )
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        OutlinedTextField(
                            value = prepMin,
                            onValueChange = { prepMin = it },
                            label = { Text("آماده‌شدن (دقیقه)") },
                            modifier = Modifier.weight(1f)
                        )
                        OutlinedTextField(
                            value = travelMin,
                            onValueChange = { travelMin = it },
                            label = { Text("حرکت بنفش (دقیقه)") },
                            modifier = Modifier.weight(1f)
                        )
                    }
                    Text("انتخاب سریع زمان حرکت:", fontSize = 12.sp)
                    Row(
                        modifier = Modifier.horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        listOf(0, 5, 10, 15, 20, 30, 45, 60).forEach { m ->
                            AssistChip(
                                onClick = { travelMin = m.toString() },
                                label = { Text("$m د") }
                            )
                        }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        FilterChip(
                            selected = repeatMode == "none",
                            onClick = { repeatMode = "none" },
                            label = { Text("بدون تکرار") }
                        )
                        FilterChip(
                            selected = repeatMode == "daily",
                            onClick = { repeatMode = "daily" },
                            label = { Text("هر روز") }
                        )
                        FilterChip(
                            selected = repeatMode == "weekly",
                            onClick = { repeatMode = "weekly" },
                            label = { Text("هفتگی") }
                        )
                    }
                }

                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    label = { Text("توضیحات / یادداشت") },
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (initial != null && initial.type != "prayer_override") {
                    TextButton(onClick = { onDelete(initial) }) {
                        Text("حذف", color = Color.Red)
                    }
                }
                Button(onClick = {
                    if (title.isBlank()) return@Button
                    val sMin = ((startHour.toIntOrNull() ?: 9).coerceIn(0, 23) * 60) +
                            (startMinute.toIntOrNull() ?: 0).coerceIn(0, 59)
                    val dur = (durationMin.toIntOrNull() ?: 60).coerceAtLeast(5)
                    val dow = LocalDate.parse(defaultIsoDate).dayOfWeek.value % 7

                    onSave(
                        ActivityEntity(
                            id = initial?.id ?: "act_${System.currentTimeMillis()}",
                            title = title.trim(),
                            type = type,
                            category = category,
                            isoDate = initial?.isoDate ?: defaultIsoDate,
                            startMin = sMin,
                            endMin = (sMin + dur).coerceAtMost(1440),
                            prepMin = (prepMin.toIntOrNull() ?: 0).coerceAtLeast(0),
                            travelMin = (travelMin.toIntOrNull() ?: 0).coerceAtLeast(0),
                            colorHex = initial?.colorHex ?: 0xFF0F766E,
                            repeatMode = repeatMode,
                            repeatDaysCsv = if (repeatMode == "weekly") dow.toString() else "",
                            remindBeforeTravelMin = 10,
                            priority = "med",
                            notes = notes,
                            isDone = initial?.isDone ?: false
                        )
                    )
                }) {
                    Text("ذخیره")
                }
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("انصراف") }
        }
    )
}
"""

# ۷. ورک‌فلوی GitHub Actions برای کامپایل خودکار APK و ارائه خروجی مستقیم
FILES[".github/workflows/build-barnameman-apk.yml"] = """name: Build BarnameMan Native Android APK

on:
  push:
  workflow_dispatch:

jobs:
  build-apk:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Source
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v3
        with:
          gradle-version: '8.7'

      - name: Build Debug APK
        run: gradle assembleDebug --no-daemon

      - name: Rename APK to BarnameMan.apk
        run: cp app/build/outputs/apk/debug/app-debug.apk BarnameMan.apk

      - name: Upload BarnameMan.apk Artifact
        uses: actions/upload-artifact@v4
        with:
          name: BarnameMan-APK
          path: BarnameMan.apk
"""

def generate_project():
    zip_filename = "BarnameMan-Native-AndroidStudio.zip"
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path, content in FILES.items():
            zf.writestr(rel_path, content)
            # همچنین ساخت فایل‌ها در پوشه جاری برای استفاده مستقیم در گیت
            os.makedirs(os.path.dirname(rel_path) or ".", exist_ok=True)
            with open(rel_path, "w", encoding="utf-8") as f:
                f.write(content)
    print(f"پروژه بومی اندروید «برنامه من» و فایل {zip_filename} با موفقیت ساخته شد!")

if __name__ == "__main__":
    generate_project()
