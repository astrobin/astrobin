import { Injectable } from "@angular/core";
import { TranslateDefaultParser } from "@ngx-translate/core";

@Injectable()
export class CustomTranslateParser extends TranslateDefaultParser {
  getValue(target: any, key: string): any {
    let value = super.getValue(target, key);

    if (value === undefined) {
      value = key;
    }

    return value;
  }
}
