package com.example.ailecturesummarizer.api;

import java.util.concurrent.TimeUnit;

import okhttp3.OkHttpClient;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

/**
 * Singleton Retrofit client for connecting to the Flask backend.
 *
 * ============================================================
 * BASE URL CONFIGURATION
 * ============================================================
 *
 * For PHYSICAL DEVICE testing:
 *   Use your computer's LAN IP address:
 *   private static final String BASE_URL = "http://192.168.1.240:5000/";
 *
 * For ANDROID EMULATOR testing:
 *   Use the special loopback address that maps to the host machine:
 *   private static final String BASE_URL = "http://10.0.2.2:5000/";
 *
 * For USB DEBUGGING with adb reverse:
 *   Run: adb reverse tcp:5000 tcp:5000
 *   Then use: private static final String BASE_URL = "http://127.0.0.1:5000/";
 *
 * The backend Flask server must be started with:
 *   app.run(host="0.0.0.0", port=5000, debug=True)
 *
 * ============================================================
 * TIMEOUTS (set generously for AI endpoints)
 * ============================================================
 * connectTimeout : 60s
 * readTimeout    : 180s  (AI summary/timestamps can take 30-90s)
 * writeTimeout   : 60s
 */
public class RetrofitClient {

    // ── Change this to 10.0.2.2 if using Android Emulator ─────────────────────
    private static final String BASE_URL = "http://192.168.1.106:5000/";


    private static volatile Retrofit retrofit;
    private static volatile ApiService apiService;

    private static volatile Retrofit aiRetrofit;
    private static volatile ApiService aiApiService;

    /** Returns a singleton ApiService instance. Thread-safe. */
    public static ApiService getApiService() {
        if (apiService == null) {
            synchronized (RetrofitClient.class) {
                if (apiService == null) {
                    apiService = buildRetrofit().create(ApiService.class);
                }
            }
        }
        return apiService;
    }

    /** Returns a singleton ApiService instance for the AI Assistant (port 8000). Thread-safe. */
    public static ApiService getAiApiService() {
        if (aiApiService == null) {
            synchronized (RetrofitClient.class) {
                if (aiApiService == null) {
                    aiApiService = buildAiRetrofit().create(ApiService.class);
                }
            }
        }
        return aiApiService;
    }

    /** Returns the base URL host, useful for direct network requests (like SSE). */
    public static String getBaseUrl() {
        return BASE_URL;
    }

    private static Retrofit buildRetrofit() {
        HttpLoggingInterceptor loggingInterceptor = new HttpLoggingInterceptor();
        loggingInterceptor.setLevel(HttpLoggingInterceptor.Level.BODY);

        OkHttpClient client = new OkHttpClient.Builder()
                .connectTimeout(60, TimeUnit.SECONDS)
                .readTimeout(180, TimeUnit.SECONDS)   // AI endpoints can be slow
                .writeTimeout(60, TimeUnit.SECONDS)
                .addInterceptor(loggingInterceptor)
                .build();

        return new Retrofit.Builder()
                .baseUrl(BASE_URL)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build();
    }

    private static Retrofit buildAiRetrofit() {
        String aiBaseUrl = BASE_URL.replace(":5000/", ":8000/");

        HttpLoggingInterceptor loggingInterceptor = new HttpLoggingInterceptor();
        loggingInterceptor.setLevel(HttpLoggingInterceptor.Level.BODY);

        OkHttpClient client = new OkHttpClient.Builder()
                .connectTimeout(60, TimeUnit.SECONDS)
                .readTimeout(180, TimeUnit.SECONDS)   // AI endpoints can be slow
                .writeTimeout(60, TimeUnit.SECONDS)
                .addInterceptor(loggingInterceptor)
                .build();

        return new Retrofit.Builder()
                .baseUrl(aiBaseUrl)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build();
    }

    /**
     * Call this if you need to change the base URL at runtime (e.g., user inputs IP).
     * Forces the next call to getApiService() and getAiApiService() to rebuild the clients.
     */
    public static void resetClient() {
        synchronized (RetrofitClient.class) {
            retrofit = null;
            apiService = null;
            aiRetrofit = null;
            aiApiService = null;
        }
    }
}