import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { TranslateLoader } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { map } from "rxjs/operators";

interface JsI18nResponse {
  catalog: any;
}

@Injectable()
export class LanguageLoader implements TranslateLoader {
  constructor(private http: HttpClient) {
  }

  getTranslation(): Observable<any> {
    return this.http.get("/jsi18n/").pipe(map((response: JsI18nResponse) => response.catalog));
  }
}
