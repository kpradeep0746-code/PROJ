package com.example.ailecturesummarizer;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.animation.AccelerateDecelerateInterpolator;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityOptionsCompat;

/**
 * Splash screen shown at app launch for 2 seconds.
 * Plays a staggered fade-in animation on logo/title/tagline,
 * then redirects to MainActivity (if logged in) or LoginActivity (if not).
 */
public class SplashActivity extends AppCompatActivity {

    private static final long SPLASH_DURATION_MS = 2000L;
    private static final long FADE_DURATION_MS    = 700L;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_splash);

        ImageView ivLogo      = findViewById(R.id.ivSplashLogo);
        TextView  tvTitle     = findViewById(R.id.tvSplashTitle);
        TextView  tvTagline   = findViewById(R.id.tvSplashTagline);

        // ── Staggered fade-in animations ──────────────────────────────────────
        if (ivLogo != null) {
            ivLogo.animate()
                    .alpha(1f)
                    .setDuration(FADE_DURATION_MS)
                    .setStartDelay(150)
                    .setInterpolator(new AccelerateDecelerateInterpolator())
                    .start();
        }

        if (tvTitle != null) {
            tvTitle.animate()
                    .alpha(1f)
                    .setDuration(FADE_DURATION_MS)
                    .setStartDelay(300)
                    .setInterpolator(new AccelerateDecelerateInterpolator())
                    .start();
        }

        if (tvTagline != null) {
            tvTagline.animate()
                    .alpha(1f)
                    .setDuration(FADE_DURATION_MS)
                    .setStartDelay(450)
                    .setInterpolator(new AccelerateDecelerateInterpolator())
                    .start();
        }

        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            SharedPreferences prefs = getSharedPreferences("noa_session", MODE_PRIVATE);
            boolean loggedIn = prefs.getBoolean("logged_in", false);
            Intent intent = new Intent(SplashActivity.this, loggedIn ? MainActivity.class : LoginActivity.class);

            // Crossfade transition using ActivityOptions
            ActivityOptionsCompat options = ActivityOptionsCompat.makeCustomAnimation(
                    SplashActivity.this,
                    android.R.anim.fade_in,
                    android.R.anim.fade_out
            );

            startActivity(intent, options.toBundle());
            finish();
        }, SPLASH_DURATION_MS);
    }
}
