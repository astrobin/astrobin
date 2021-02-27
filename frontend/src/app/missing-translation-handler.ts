import { MissingTranslationHandler, MissingTranslationHandlerParams } from "@ngx-translate/core";

export class CustomMissingTranslationHandler implements MissingTranslationHandler {
  handle(params: MissingTranslationHandlerParams) {
    return params.key;
  }
}
