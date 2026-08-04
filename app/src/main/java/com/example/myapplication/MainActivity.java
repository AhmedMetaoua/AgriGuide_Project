package com.example.myapplication;

import android.Manifest;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.util.Base64;
import android.view.View;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageCapture;
import androidx.camera.core.ImageCaptureException;
import androidx.camera.core.Preview;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.core.app.ActivityCompat;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.core.content.ContextCompat;
import androidx.lifecycle.ViewModelProvider;

import com.bumptech.glide.Glide;
import com.example.myapplication.adapter.HistoryAdapter;
import com.example.myapplication.databinding.ActivityMainBinding;
import com.example.myapplication.databinding.BottomSheetHistoryBinding;
import com.example.myapplication.model.InsectAnalysis;
import com.example.myapplication.viewmodel.InsectViewModel;
import com.google.android.material.bottomsheet.BottomSheetDialog;
import com.google.common.util.concurrent.ListenableFuture;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.util.ArrayList;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * AgriGuard - Assistant Agricole de Précision.
 * Cette classe orchestre la capture CameraX, l'analyse IA et les alertes visuelles.
 */
public class MainActivity extends AppCompatActivity {

    private ActivityMainBinding binding;
    private InsectViewModel viewModel;
    private ImageCapture imageCapture;
    private ExecutorService cameraExecutor;

    private static final String CHANNEL_ID = "agri_alert_channel";
    private static final int NOTIFICATION_ID = 101;
    private static final int REQUEST_CODE_PERMISSIONS = 10;
    private static final int PICK_IMAGE_REQUEST = 11;
    
    // Permissions adaptées à la version d'Android (Camera + Notifications pour API 33+)
    private static final String[] REQUIRED_PERMISSIONS = Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU 
            ? new String[]{Manifest.permission.CAMERA, Manifest.permission.POST_NOTIFICATIONS}
            : new String[]{Manifest.permission.CAMERA};

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        viewModel = new ViewModelProvider(this).get(InsectViewModel.class);
        cameraExecutor = Executors.newSingleThreadExecutor();

        // Background image
        Glide.with(this)
                .load("https://images.unsplash.com/photo-1501004318641-729e8c3396ee?q=80&w=1200")
                .into(binding.ivPlaceholder);

        createNotificationChannel();

        setupObservers();
        setupListeners();

        // Initial state
        showHome();
    }

    private void setupObservers() {
        // État de chargement
        viewModel.getIsLoading().observe(this, isLoading -> {
            binding.loadingLayout.setVisibility(isLoading ? View.VISIBLE : View.GONE);
            binding.btnCapture.setEnabled(!isLoading);
            binding.ivScanFrame.setVisibility(isLoading ? View.GONE : View.VISIBLE);
        });

        // Message de titre du statut
        viewModel.getStatusMessage().observe(this, status -> {
            if (status != null && !status.isEmpty()) {
                binding.tvLoadingStatus.setText(status);
            }
        });

        // Détails de l'étape en cours (ex: "Envoi de la clé API...")
        viewModel.getStepDetail().observe(this, detail -> {
            if (detail != null && !detail.isEmpty()) {
                binding.tvStepInfo.setText(detail);
            }
        });

        // Gestion des erreurs
        viewModel.getErrorMessage().observe(this, error -> {
            if (error != null) {
                Toast.makeText(this, error, Toast.LENGTH_LONG).show();
            }
        });

        // Résultat de l'analyse
        viewModel.getAnalysisResult().observe(this, analysis -> {
            if (analysis != null) {
                displayResult(analysis);
            }
        });
    }

    private void showHome() {
        binding.homeContainer.setVisibility(View.VISIBLE);
        binding.cameraContainer.setVisibility(View.GONE);
        binding.resultCard.setVisibility(View.GONE);
        binding.bottomNavigation.setVisibility(View.VISIBLE);
        resetToNormalTheme();
    }

    private void showCamera() {
        if (allPermissionsGranted()) {
            binding.homeContainer.setVisibility(View.GONE);
            binding.cameraContainer.setVisibility(View.VISIBLE);
            binding.bottomNavigation.setVisibility(View.GONE);
            startCamera();
        } else {
            ActivityCompat.requestPermissions(this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS);
        }
    }

    private void setupListeners() {
        binding.cardCamera.setOnClickListener(v -> showCamera());
        binding.cardLibrary.setOnClickListener(v -> openGallery());
        binding.btnBackHome.setOnClickListener(v -> showHome());
        
        binding.btnCapture.setOnClickListener(v -> takePhoto());
        binding.btnClose.setOnClickListener(v -> {
            binding.resultCard.setVisibility(View.GONE);
            resetToNormalTheme();
            viewModel.resetResult();
        });
        
        binding.bottomNavigation.setOnItemSelectedListener(item -> {
            if (item.getItemId() == R.id.nav_history) {
                showHistoryBottomSheet();
                return true;
            }
            return true;
        });
    }

    private void showHistoryBottomSheet() {
        BottomSheetDialog bottomSheetDialog = new BottomSheetDialog(this);
        BottomSheetHistoryBinding sheetBinding = BottomSheetHistoryBinding.inflate(getLayoutInflater());
        bottomSheetDialog.setContentView(sheetBinding.getRoot());

        HistoryAdapter adapter = new HistoryAdapter();
        sheetBinding.rvHistory.setAdapter(adapter);

        viewModel.getHistory().observe(this, adapter::setHistory);

        bottomSheetDialog.show();
    }

    private void openGallery() {
        android.content.Intent intent = new android.content.Intent(android.content.Intent.ACTION_PICK);
        intent.setType("image/*");
        startActivityForResult(intent, PICK_IMAGE_REQUEST);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, android.content.Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == PICK_IMAGE_REQUEST && resultCode == RESULT_OK && data != null && data.getData() != null) {
            try {
                android.net.Uri imageUri = data.getData();
                java.io.InputStream imageStream = getContentResolver().openInputStream(imageUri);
                Bitmap selectedImage = BitmapFactory.decodeStream(imageStream);
                String base64 = encodeImage(selectedImage);
                viewModel.analyzeImage(base64);
            } catch (java.io.FileNotFoundException e) {
                Toast.makeText(this, "Erreur lors de la sélection de l'image", Toast.LENGTH_SHORT).show();
            }
        }
    }

    private void startCamera() {
        ListenableFuture<ProcessCameraProvider> cameraProviderFuture = ProcessCameraProvider.getInstance(this);

        cameraProviderFuture.addListener(() -> {
            try {
                ProcessCameraProvider cameraProvider = cameraProviderFuture.get();

                Preview preview = new Preview.Builder().build();
                preview.setSurfaceProvider(binding.viewFinder.getSurfaceProvider());

                imageCapture = new ImageCapture.Builder()
                        .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                        .build();

                CameraSelector cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA;

                cameraProvider.unbindAll();
                cameraProvider.bindToLifecycle(this, cameraSelector, preview, imageCapture);

            } catch (ExecutionException | InterruptedException e) {
                Toast.makeText(this, getString(R.string.erreur_camera), Toast.LENGTH_SHORT).show();
            }
        }, ContextCompat.getMainExecutor(this));
    }

    private void takePhoto() {
        if (imageCapture == null) return;

        File photoFile = new File(getExternalCacheDir(), "scan_insect.jpg");
        ImageCapture.OutputFileOptions outputOptions = new ImageCapture.OutputFileOptions.Builder(photoFile).build();

        imageCapture.takePicture(outputOptions, ContextCompat.getMainExecutor(this), new ImageCapture.OnImageSavedCallback() {
            @Override
            public void onImageSaved(@NonNull ImageCapture.OutputFileResults outputFileResults) {
                Bitmap bitmap = BitmapFactory.decodeFile(photoFile.getAbsolutePath());
                String base64 = encodeImage(bitmap);
                viewModel.analyzeImage(base64);
            }

            @Override
            public void onError(@NonNull ImageCaptureException exception) {
                Toast.makeText(MainActivity.this, getString(R.string.erreur_capture, exception.getMessage()), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private String encodeImage(Bitmap bitmap) {
        // Redimensionner pour optimiser le transfert API
        Bitmap resizedBitmap = Bitmap.createScaledBitmap(bitmap, 800, 800, true);
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        resizedBitmap.compress(Bitmap.CompressFormat.JPEG, 80, baos);
        byte[] b = baos.toByteArray();
        return Base64.encodeToString(b, Base64.NO_WRAP);
    }

    private void displayResult(InsectAnalysis analysis) {
        // Cacher la caméra pour voir le résultat sur le fond
        binding.cameraContainer.setVisibility(View.GONE);
        binding.resultCard.setVisibility(View.VISIBLE);
        
        if (analysis.getInsectName() == null || analysis.getInsectName().isEmpty()) {
            binding.tvInsectName.setText("Insecte Inconnu");
        } else {
            binding.tvInsectName.setText(analysis.getInsectName());
        }

        binding.tvImpactDetails.setText(analysis.getAgriculturalImpact());

        // Log pour débogage
        android.util.Log.d("AgriGuard", "Displaying result: " + analysis.getInsectName());

        if (analysis.isHarmful()) {
            binding.ivInsectStatus.setImageResource(android.R.drawable.ic_dialog_alert);
            binding.ivInsectStatus.setColorFilter(ContextCompat.getColor(this, R.color.alert_accent));
            triggerRedAlert();
            showNotification(analysis.getInsectName());
        } else {
            binding.ivInsectStatus.setImageResource(android.R.drawable.ic_dialog_info);
            binding.ivInsectStatus.setColorFilter(ContextCompat.getColor(this, R.color.primary_green));
            resetToNormalTheme();
        }
    }

    private void triggerRedAlert() {
        binding.resultCard.setStrokeColor(android.content.res.ColorStateList.valueOf(ContextCompat.getColor(this, R.color.alert_accent)));
        binding.resultCard.setStrokeWidth(4);
        binding.tvInsectName.setTextColor(ContextCompat.getColor(this, R.color.alert_accent));
        binding.vOverlay.setBackgroundColor(ContextCompat.getColor(this, R.color.alert_dark_red));
        binding.btnCapture.setBackgroundTintList(android.content.res.ColorStateList.valueOf(ContextCompat.getColor(this, R.color.alert_accent)));
        getWindow().setStatusBarColor(ContextCompat.getColor(this, R.color.alert_dark_red));
        vibrate();
    }

    private void vibrate() {
        android.os.Vibrator v = (android.os.Vibrator) getSystemService(android.content.Context.VIBRATOR_SERVICE);
        if (v != null) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                v.vibrate(android.os.VibrationEffect.createOneShot(500, android.os.VibrationEffect.DEFAULT_AMPLITUDE));
            } else {
                v.vibrate(500);
            }
        }
    }

    private void resetToNormalTheme() {
        binding.resultCard.setStrokeColor(android.content.res.ColorStateList.valueOf(ContextCompat.getColor(this, R.color.accent_gold)));
        binding.resultCard.setStrokeWidth(0);
        binding.tvInsectName.setTextColor(ContextCompat.getColor(this, R.color.primary_green));
        binding.vOverlay.setBackgroundColor(Color.parseColor("#40000000"));
        binding.btnCapture.setBackgroundTintList(android.content.res.ColorStateList.valueOf(ContextCompat.getColor(this, R.color.accent_gold)));
        getWindow().setStatusBarColor(ContextCompat.getColor(this, R.color.primary_dark_green));
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "Alertes AgriGuard", NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("Canal pour les alertes nuisibles");
            NotificationManager nm = getSystemService(NotificationManager.class);
            if (nm != null) nm.createNotificationChannel(channel);
        }
    }

    private void showNotification(String insectName) {
        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_alert)
                .setContentTitle(getString(R.string.alerte_nuisible))
                .setContentText(getString(R.string.alerte_description, insectName))
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setVibrate(new long[]{0, 500, 200, 500})
                .setAutoCancel(true);

        NotificationManagerCompat nmc = NotificationManagerCompat.from(this);
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED) {
            nmc.notify(NOTIFICATION_ID, builder.build());
        }
    }

    private boolean allPermissionsGranted() {
        for (String permission : REQUIRED_PERMISSIONS) {
            if (ContextCompat.checkSelfPermission(this, permission) != PackageManager.PERMISSION_GRANTED) {
                return false;
            }
        }
        return true;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            if (allPermissionsGranted()) {
                startCamera();
            } else {
                Toast.makeText(this, getString(R.string.permissions_refusees), Toast.LENGTH_SHORT).show();
                finish();
            }
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        cameraExecutor.shutdown();
    }
}
