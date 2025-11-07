package com.xlx.pyqt6.enums;

import lombok.Getter;

@Getter
public enum ResultCodeEnum {

    // 成功
    SUCCESS(200, "操作成功"),

    // 通用错误
    BAD_REQUEST(400, "请求参数错误"),
    UNAUTHORIZED(401, "未授权"),
    FORBIDDEN(403, "禁止访问"),
    NOT_FOUND(404, "资源不存在"),
    SERVER_ERROR(500, "服务器内部错误"),

    // 业务错误
    DATA_NOT_EXIST(1001, "数据不存在"),
    DUPLICATE_DATA(1002, "数据已存在"),
    JWT_TOKEN_EXPIRED(2003, "JWT Token Expired"),
    JWT_TOKEN_INVALID(2004, "JWT Token Invalid"),
    JWT_TOKEN_ERROR(2005, "JWT Token Error"),
    ACCOUNT_IS_DISABLED(3006,"账户已停用"),
    ACCOUNT_IS_UNAVAILABLE(3007,"用户名或密码不正确"),
    ;

    private final Integer code;
    private final String message;

    ResultCodeEnum(Integer code, String message) {
        this.code = code;
        this.message = message;
    }

   /* public Integer getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }*/
}
