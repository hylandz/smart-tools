package com.xlx.pyqt6.utils;

import com.alibaba.fastjson2.JSON;
import com.xlx.pyqt6.entity.VersionVO;
import lombok.extern.slf4j.Slf4j;

import javax.swing.*;
import java.io.*;
import java.util.Objects;

@Slf4j
public class FileUtil {



    public static VersionVO readVersion(String filename){
        try {
            BufferedReader br = new BufferedReader(new FileReader(filename));
            StringBuilder jsonString = new StringBuilder();
            String line;
            while ((line = br.readLine()) !=null){
                jsonString.append(line);
            }
            br.close();

            return JSON.parseObject(jsonString.toString(), VersionVO.class);
        } catch (IOException e) {
           log.error(e.getMessage());
            throw new RuntimeException(e);
        }
    }

    public static void main(String[] args) {
        VersionVO ver = FileUtil.readVersion("jt808.json");
        log.info(JSON.toJSONString(ver));
    }
}
