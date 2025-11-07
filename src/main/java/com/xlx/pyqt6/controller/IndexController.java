package com.xlx.pyqt6.controller;

import com.xlx.pyqt6.entity.ResultVO;
import com.xlx.pyqt6.entity.VersionVO;
import com.xlx.pyqt6.utils.FileUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

@Slf4j
@Controller()
@RequestMapping("/jt808")
public class IndexController {

    @RequestMapping("/get_version.json")
    @ResponseBody
    public ResultVO<Object> getVersion(){
        VersionVO ver = FileUtil.readVersion("jt808.json");
        // log.info("version:{}", ver);
        return ResultVO.success().data(ver);
    }

    @RequestMapping("/")
    @ResponseBody
    public ResultVO<Void> index(){
        return ResultVO.success();
    }
}
