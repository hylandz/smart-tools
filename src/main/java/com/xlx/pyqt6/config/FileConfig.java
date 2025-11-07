package com.xlx.pyqt6.config;

import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@Configuration
public class FileConfig {

    @Value("${app.file.upload-dir}")
    private String uploadDir;

    @PostConstruct
    public void createUploadDirectory() {
        Path uploadPath = Paths.get(uploadDir);
        System.out.println("uploadPath=" + uploadPath);
        try {
            Files.createDirectories(uploadPath);
        } catch (IOException e) {
            throw new RuntimeException("无法创建上传目录", e);
        }
    }
}