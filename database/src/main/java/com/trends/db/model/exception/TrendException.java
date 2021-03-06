package com.trends.db.model.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(HttpStatus.NOT_FOUND)
public class TrendException extends RuntimeException {

  public TrendException(final String message) {

    super(message);
  }
}
