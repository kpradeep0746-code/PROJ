package com.example.ailecturesummarizer;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.View;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.example.ailecturesummarizer.database.NoaDatabaseHelper;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.textfield.TextInputEditText;

/**
 * Login screen. Authenticates against the local SQLite database (NoaDatabaseHelper).
 * On success, saves session to SharedPreferences and navigates to MainActivity.
 */
public class LoginActivity extends AppCompatActivity {

    private TextInputEditText etEmail;
    private TextInputEditText etPassword;
    private MaterialButton btnLogin;
    private View tvGoToRegister;

    private NoaDatabaseHelper dbHelper;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // If already logged in, skip directly to main screen
        SharedPreferences prefs = getSharedPreferences("noa_session", MODE_PRIVATE);
        if (prefs.getBoolean("logged_in", false)) {
            goToMain();
            return;
        }

        setContentView(R.layout.activity_login);

        dbHelper = NoaDatabaseHelper.getInstance(this);

        etEmail       = findViewById(R.id.etEmail);
        etPassword    = findViewById(R.id.etPassword);
        btnLogin      = findViewById(R.id.btnLogin);
        tvGoToRegister = findViewById(R.id.tvGoToRegister);

        btnLogin.setOnClickListener(v -> handleLogin());
        tvGoToRegister.setOnClickListener(v ->
                startActivity(new Intent(LoginActivity.this, RegisterActivity.class)));
    }

    private void handleLogin() {
        String email    = etEmail.getText() != null ? etEmail.getText().toString().trim() : "";
        String password = etPassword.getText() != null ? etPassword.getText().toString() : "";

        if (TextUtils.isEmpty(email) || TextUtils.isEmpty(password)) {
            Toast.makeText(this, "Please fill in all fields", Toast.LENGTH_SHORT).show();
            return;
        }

        boolean success = dbHelper.authenticateUser(email, password);
        if (success) {
            // Persist session
            getSharedPreferences("noa_session", MODE_PRIVATE)
                    .edit()
                    .putBoolean("logged_in", true)
                    .putString("user_email", email)
                    .apply();
            goToMain();
        } else {
            Toast.makeText(this, "Invalid email or password", Toast.LENGTH_SHORT).show();
        }
    }

    private void goToMain() {
        startActivity(new Intent(LoginActivity.this, MainActivity.class));
        finish();
    }
}
