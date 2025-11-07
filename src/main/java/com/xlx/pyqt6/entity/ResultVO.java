package com.xlx.pyqt6.entity;
import com.xlx.pyqt6.enums.ResultCodeEnum;
import lombok.Data;

import java.io.Serial;
import java.io.Serializable;


@Data
public class ResultVO<T> implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;
    // 状态码
    private Integer code;
    // 提示信息
    private String message;
    // 时间戳（可选）
    private T data;
    //
    private Long timestamp;

    private ResultVO() {}

    // 私有构造方法，强制通过静态方法创建实例
    private ResultVO(Integer code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
        this.timestamp = System.currentTimeMillis();
    }

    // 成功
    public static <T> ResultVO<T> success(T data) {
        return new ResultVO<>(ResultCodeEnum.SUCCESS.getCode(),ResultCodeEnum.SUCCESS.getMessage(),data);
    }

    public static <T> ResultVO<T> success() {
        return new ResultVO<>(ResultCodeEnum.SUCCESS.getCode(),ResultCodeEnum.SUCCESS.getMessage(),null);
    }

    // 失败
    public static <T> ResultVO<T> fail(ResultCodeEnum resultCodeEnum) {
        return new ResultVO<>(resultCodeEnum.getCode(), resultCodeEnum.getMessage(), null);
    }

    public static <T> ResultVO<T> fail(Integer code, String message) {
        return new ResultVO<>(code,message,null);
    }

    // 链式编程
    public ResultVO<T> code(Integer code){
        this.setCode(code);
        return this;
    }
    public ResultVO<T> message(String message){
        this.setMessage(message);
        return this;
    }
    public ResultVO<T> data(T data){
        this.setData(data);
        return this;
    }

}

