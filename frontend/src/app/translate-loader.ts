import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { environment } from "@env/environment";
import { TranslatePoHttpLoader } from "@fjnr/ngx-translate-po-http-loader";
import { JsonApiService } from "@shared/services/api/classic/json/json-api.service";
import { TimeagoIntl } from "ngx-timeago";
import { strings as timeagoAf } from "ngx-timeago/language-strings/af";
import { strings as timeagoAr } from "ngx-timeago/language-strings/ar";
import { strings as timeagoAz } from "ngx-timeago/language-strings/az";
import { strings as timeagoBg } from "ngx-timeago/language-strings/bg";
import { strings as timeagoBs } from "ngx-timeago/language-strings/bs";
import { strings as timeagoCa } from "ngx-timeago/language-strings/ca";
import { strings as timeagoCs } from "ngx-timeago/language-strings/cs";
import { strings as timeagoCy } from "ngx-timeago/language-strings/cy";
import { strings as timeagoDa } from "ngx-timeago/language-strings/da";
import { strings as timeagoDe } from "ngx-timeago/language-strings/de";
import { strings as timeagoDv } from "ngx-timeago/language-strings/dv";
import { strings as timeagoEl } from "ngx-timeago/language-strings/el";
import { strings as timeagoEn } from "ngx-timeago/language-strings/en";
import { strings as timeagoEs } from "ngx-timeago/language-strings/es";
import { strings as timeagoEt } from "ngx-timeago/language-strings/et";
import { strings as timeagoEu } from "ngx-timeago/language-strings/eu";
import { strings as timeagoFa } from "ngx-timeago/language-strings/fa";
import { strings as timeagoFi } from "ngx-timeago/language-strings/fi";
import { strings as timeagoFr } from "ngx-timeago/language-strings/fr";
import { strings as timeagoGl } from "ngx-timeago/language-strings/gl";
import { strings as timeagoHe } from "ngx-timeago/language-strings/he";
import { strings as timeagoHr } from "ngx-timeago/language-strings/hr";
import { strings as timeagoHu } from "ngx-timeago/language-strings/hu";
import { strings as timeagoHy } from "ngx-timeago/language-strings/hy";
import { strings as timeagoId } from "ngx-timeago/language-strings/id";
import { strings as timeagoIs } from "ngx-timeago/language-strings/is";
import { strings as timeagoIt } from "ngx-timeago/language-strings/it";
import { strings as timeagoJa } from "ngx-timeago/language-strings/ja";
import { strings as timeagoJv } from "ngx-timeago/language-strings/jv";
import { strings as timeagoKo } from "ngx-timeago/language-strings/ko";
import { strings as timeagoKy } from "ngx-timeago/language-strings/ky";
import { strings as timeagoLt } from "ngx-timeago/language-strings/lt";
import { strings as timeagoLv } from "ngx-timeago/language-strings/lv";
import { strings as timeagoMk } from "ngx-timeago/language-strings/mk";
import { strings as timeagoNl } from "ngx-timeago/language-strings/nl";
import { strings as timeagoNo } from "ngx-timeago/language-strings/no";
import { strings as timeagoPl } from "ngx-timeago/language-strings/pl";
import { strings as timeagoPt } from "ngx-timeago/language-strings/pt";
import { strings as timeagoPtBr } from "ngx-timeago/language-strings/pt-br";
import { strings as timeagoRo } from "ngx-timeago/language-strings/ro";
import { strings as timeagoRs } from "ngx-timeago/language-strings/rs";
import { strings as timeagoRu } from "ngx-timeago/language-strings/ru";
import { strings as timeagoRw } from "ngx-timeago/language-strings/rw";
import { strings as timeagoSi } from "ngx-timeago/language-strings/si";
import { strings as timeagoSk } from "ngx-timeago/language-strings/sk";
import { strings as timeagoSl } from "ngx-timeago/language-strings/sl";
import { strings as timeagoSr } from "ngx-timeago/language-strings/sr";
import { strings as timeagoSv } from "ngx-timeago/language-strings/sv";
import { strings as timeagoTh } from "ngx-timeago/language-strings/th";
import { strings as timeagoTr } from "ngx-timeago/language-strings/tr";
import { strings as timeagoUk } from "ngx-timeago/language-strings/uk";
import { strings as timeagoUz } from "ngx-timeago/language-strings/uz";
import { strings as timeagoVi } from "ngx-timeago/language-strings/vi";
import { strings as timeagoZhCn } from "ngx-timeago/language-strings/zh-CN";
import { strings as timeagoZhTw } from "ngx-timeago/language-strings/zh-TW";
import { forkJoin, Observable } from "rxjs";
import { catchError, map, switchMap } from "rxjs/operators";

declare const VERSION: string;

@Injectable()
export class LanguageLoader extends TranslatePoHttpLoader {
  constructor(public http: HttpClient, public jsonApi: JsonApiService) {
    super(http);
  }

  ngJsonTranslations$ = (lang: string): Observable<object> =>
    this.http.get(`/assets/i18n/${lang}.json?version=${VERSION}`);

  ngTranslations$ = (lang: string): Observable<object> =>
    this.http
      .get(`/assets/i18n/${lang}.po?version=${VERSION}`, {
        responseType: "text"
      })
      .pipe(map((contents: string) => this.parse(contents)));

  classicTranslations$ = (lang: string): Observable<object> =>
    this.jsonApi.getBackendConfig().pipe(
      switchMap(backendConfig =>
        this.http
          .get(`${environment.classicApiUrl}/json-api/i18n/messages/${lang}/?version=${backendConfig.i18nHash}`, {
            responseType: "text"
          })
          .pipe(map((contents: string) => this.parse(contents)))
      )
    );

  getTranslation(lang: string): Observable<any> {
    const backends = [
      this.classicTranslations$(lang),
      this.ngTranslations$(lang).pipe(catchError(() => this.ngTranslations$("en")))
    ];

    if (["pt"].indexOf(lang) > -1) {
      backends.push(this.ngJsonTranslations$(lang).pipe(catchError(() => this.ngJsonTranslations$("en"))));
    }

    backends.push();
    return forkJoin(backends).pipe(
      map(results => {
        const classicTranslations = results[0];
        const ngTranslations = results[1];
        const ngJsonTranslations = results[2];

        Object.keys(classicTranslations).forEach(key => {
          if (classicTranslations[key] === "") {
            classicTranslations[key] = key;
          }
        });

        if (ngJsonTranslations) {
          Object.keys(ngJsonTranslations).forEach(key => {
            if (ngJsonTranslations[key] === "") {
              ngJsonTranslations[key] = key;
            }
          });
        }

        Object.keys(ngTranslations).forEach(key => {
          if (ngTranslations[key] === "") {
            if (ngJsonTranslations) {
              ngTranslations[key] = ngJsonTranslations[key];
            } else {
              ngTranslations[key] = key;
            }
          }
        });

        return {
          ...ngJsonTranslations,
          ...ngTranslations,
          ...classicTranslations
        };
      })
    );
  }

  parse(contents: string): any {
    const translations = super.parse(contents);
    const mapped = {};

    Object.keys(translations).forEach(key => {
      const regex = /%\((.*?)\)s/g;
      const replacement = "{{$1}}";
      mapped[key.replace(regex, replacement)] = translations[key].replace(regex, replacement);
    });

    return mapped;
  }
}

export function setTimeagoIntl(timeagoIntl: TimeagoIntl, language: string): void {
  switch (language) {
    case "af":
      timeagoIntl.strings = timeagoAf;
      break;
    case "ar":
      timeagoIntl.strings = timeagoAr;
      break;
    case "az":
      timeagoIntl.strings = timeagoAz;
      break;
    case "bg":
      timeagoIntl.strings = timeagoBg;
      break;
    case "bs":
      timeagoIntl.strings = timeagoBs;
      break;
    case "ca":
      timeagoIntl.strings = timeagoCa;
      break;
    case "cs":
      timeagoIntl.strings = timeagoCs;
      break;
    case "cy":
      timeagoIntl.strings = timeagoCy;
      break;
    case "da":
      timeagoIntl.strings = timeagoDa;
      break;
    case "de":
      timeagoIntl.strings = timeagoDe;
      break;
    case "dv":
      timeagoIntl.strings = timeagoDv;
      break;
    case "el":
      timeagoIntl.strings = timeagoEl;
      break;
    case "en":
      timeagoIntl.strings = timeagoEn;
      break;
    case "es":
      timeagoIntl.strings = timeagoEs;
      break;
    case "et":
      timeagoIntl.strings = timeagoEt;
      break;
    case "eu":
      timeagoIntl.strings = timeagoEu;
      break;
    case "fa":
      timeagoIntl.strings = timeagoFa;
      break;
    case "fi":
      timeagoIntl.strings = timeagoFi;
      break;
    case "fr":
      timeagoIntl.strings = timeagoFr;
      break;
    case "gl":
      timeagoIntl.strings = timeagoGl;
      break;
    case "he":
      timeagoIntl.strings = timeagoHe;
      break;
    case "hr":
      timeagoIntl.strings = timeagoHr;
      break;
    case "hu":
      timeagoIntl.strings = timeagoHu;
      break;
    case "hy":
      timeagoIntl.strings = timeagoHy;
      break;
    case "id":
      timeagoIntl.strings = timeagoId;
      break;
    case "is":
      timeagoIntl.strings = timeagoIs;
      break;
    case "it":
      timeagoIntl.strings = timeagoIt;
      break;
    case "ja":
      timeagoIntl.strings = timeagoJa;
      break;
    case "jv":
      timeagoIntl.strings = timeagoJv;
      break;
    case "ko":
      timeagoIntl.strings = timeagoKo;
      break;
    case "ky":
      timeagoIntl.strings = timeagoKy;
      break;
    case "lt":
      timeagoIntl.strings = timeagoLt;
      break;
    case "lv":
      timeagoIntl.strings = timeagoLv;
      break;
    case "mk":
      timeagoIntl.strings = timeagoMk;
      break;
    case "nl":
      timeagoIntl.strings = timeagoNl;
      break;
    case "no":
      timeagoIntl.strings = timeagoNo;
      break;
    case "pl":
      timeagoIntl.strings = timeagoPl;
      break;
    case "pt":
      timeagoIntl.strings = timeagoPt;
      break;
    case "pt-br":
      timeagoIntl.strings = timeagoPtBr;
      break;
    case "ro":
      timeagoIntl.strings = timeagoRo;
      break;
    case "rs":
      timeagoIntl.strings = timeagoRs;
      break;
    case "ru":
      timeagoIntl.strings = timeagoRu;
      break;
    case "rw":
      timeagoIntl.strings = timeagoRw;
      break;
    case "si":
      timeagoIntl.strings = timeagoSi;
      break;
    case "sk":
      timeagoIntl.strings = timeagoSk;
      break;
    case "sl":
      timeagoIntl.strings = timeagoSl;
      break;
    case "sr":
      timeagoIntl.strings = timeagoSr;
      break;
    case "sv":
      timeagoIntl.strings = timeagoSv;
      break;
    case "th":
      timeagoIntl.strings = timeagoTh;
      break;
    case "tr":
      timeagoIntl.strings = timeagoTr;
      break;
    case "uk":
      timeagoIntl.strings = timeagoUk;
      break;
    case "uz":
      timeagoIntl.strings = timeagoUz;
      break;
    case "vi":
      timeagoIntl.strings = timeagoVi;
      break;
    case "zh-CN":
      timeagoIntl.strings = timeagoZhCn;
      break;
    case "zh-TW":
      timeagoIntl.strings = timeagoZhTw;
      break;
    default:
      timeagoIntl.strings = timeagoEn;
  }

  timeagoIntl.changes.next();
}
