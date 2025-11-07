package com.xlx.pyqt6.controller;

import cn.xuyanwu.spring.file.storage.FileStorageService;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.FilenameUtils;
import org.apache.hc.core5.http.io.entity.FileEntity;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.nio.file.Path;
import java.nio.file.Paths;
@Slf4j
@RestController
@RequestMapping("/download")
public class FileDownloadController {


    @GetMapping("/file")
    public ResponseEntity<Resource> downloadFile(@RequestParam String filename) {
        try {
            // 文件存储路径（根据实际情况调整）
            String fileDirectory = "uploads/";
            Path filePath = Paths.get(fileDirectory).resolve(filename).normalize();
            Resource resource = new UrlResource(filePath.toUri());
            String url = String.valueOf(resource.getURL());
            log.info("请求文件下载：{}", url);
            // 检查文件是否存在
            if (!resource.exists()) {
                return ResponseEntity.notFound().build();
            }

            // 确定内容类型
            String contentType = determineContentType(filename);

            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType(contentType))
                    .header(HttpHeaders.CONTENT_DISPOSITION,
                            "attachment; filename=\"" + resource.getFilename() + "\"")
                    .body(resource);

        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }


    private String determineContentType(String filename) {
        String extension = FilenameUtils.getExtension(filename).toLowerCase();
        return switch (extension) {
            case "pdf" -> "application/pdf";
            case "txt" -> "text/plain";
            case "jpg", "jpeg" -> "image/jpeg";
            case "png" -> "image/png";
            case "xlsx" -> "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
            case "docx" -> "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
            default -> "application/octet-stream";
        };
    }

}
