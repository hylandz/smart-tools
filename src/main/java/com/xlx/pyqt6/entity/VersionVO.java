package com.xlx.pyqt6.entity;

import com.alibaba.fastjson2.annotation.JSONField;
import lombok.Data;
import lombok.Getter;
import lombok.Setter;

@Data
@Getter
@Setter
public class VersionVO {
    @JSONField(name = "latest_version")
    private String latestVersion;

    private String description;
    @JSONField(name = "download_url")
    private String downloadUrl;

    public VersionVO() {}

}
