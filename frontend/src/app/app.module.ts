import { registerLocaleData } from "@angular/common";
import { HttpClient, HttpClientModule } from "@angular/common/http";
import localeArabic from "@angular/common/locales/ar";
import localeGerman from "@angular/common/locales/de";
import localeGreek from "@angular/common/locales/el";
import localeEnglish from "@angular/common/locales/en";
import localeBritishEnglish from "@angular/common/locales/en-GB";
import localeSpanish from "@angular/common/locales/es";
import localeFinnish from "@angular/common/locales/fi";
import localeFrench from "@angular/common/locales/fr";
import localeItalian from "@angular/common/locales/it";
import localeJapanese from "@angular/common/locales/ja";
import localeDutch from "@angular/common/locales/nl";
import localePolish from "@angular/common/locales/pl";
import localePortuguese from "@angular/common/locales/pt";
import localeRussian from "@angular/common/locales/ru";
import localeAlbanian from "@angular/common/locales/sq";
import localeTurkish from "@angular/common/locales/tr";
import { NgModule } from "@angular/core";
import { BrowserModule, Title } from "@angular/platform-browser";
import { BrowserAnimationsModule } from "@angular/platform-browser/animations";
import { AppComponent } from "@app/app.component";
import { appStateEffects, appStateReducers } from "@app/store/state";
import { CustomTranslateParser } from "@app/translate-parser";
import { environment } from "@env/environment";
import { FaIconLibrary } from "@fortawesome/angular-fontawesome";
import {
  faAsterisk,
  faBarcode,
  faBars,
  faBook,
  faBookmark,
  faCertificate,
  faChartBar,
  faComments,
  faCreditCard,
  faEdit,
  faEnvelope,
  faEye,
  faFlag,
  faGlobe,
  faHammer,
  faImage,
  faImages,
  faInbox,
  faInfo,
  faKey,
  faListOl,
  faLock,
  faQuestion,
  fas,
  faSearch,
  faSignOutAlt,
  faSortAmountDown,
  faStar,
  faTasks,
  faTrophy,
  faUpload,
  faUsers
} from "@fortawesome/free-solid-svg-icons";
import { EffectsModule } from "@ngrx/effects";
import { StoreModule } from "@ngrx/store";
import { StoreDevtoolsModule } from "@ngrx/store-devtools";
import { MissingTranslationHandler, TranslateLoader, TranslateModule, TranslateParser } from "@ngx-translate/core";
import { JsonApiService } from "@shared/services/api/classic/json/json-api.service";
import { WindowRefService } from "@shared/services/window-ref.service";
import { SharedModule } from "@shared/shared.module";
import { CookieService } from "ngx-cookie-service";
import { TimeagoCustomFormatter, TimeagoFormatter, TimeagoIntl, TimeagoModule } from "ngx-timeago";
import { AppRoutingModule } from "./app-routing.module";
import { CustomMissingTranslationHandler } from "./missing-translation-handler";
import { LanguageLoader } from "./translate-loader";

// Supported languages
registerLocaleData(localeEnglish);
registerLocaleData(localeBritishEnglish);
registerLocaleData(localeFrench);
registerLocaleData(localeGerman);
registerLocaleData(localeItalian);
registerLocaleData(localeSpanish);
registerLocaleData(localePortuguese);

// Community languages
registerLocaleData(localeArabic);
registerLocaleData(localeGreek);
registerLocaleData(localeFinnish);
registerLocaleData(localeJapanese);
registerLocaleData(localeDutch);
registerLocaleData(localePolish);
registerLocaleData(localeRussian);
registerLocaleData(localeAlbanian);
registerLocaleData(localeTurkish);

export function initFontAwesome(iconLibrary: FaIconLibrary) {
  iconLibrary.addIconPacks(fas);
  iconLibrary.addIcons(
    faAsterisk,
    faBarcode,
    faBook,
    faBookmark,
    faChartBar,
    faComments,
    faEdit,
    faEnvelope,
    faEye,
    faFlag,
    faGlobe,
    faHammer,
    faImage,
    faImages,
    faInbox,
    faInfo,
    faKey,
    faListOl,
    faLock,
    faBars,
    faQuestion,
    faSearch,
    faSignOutAlt,
    faSortAmountDown,
    faStar,
    faTasks,
    faTrophy,
    faUpload,
    faUsers,
    faCertificate,
    faCreditCard
  );
}

@NgModule({
  imports: [
    // Angular.
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,

    // Dependencies.
    StoreModule.forRoot(appStateReducers),
    StoreDevtoolsModule.instrument({
      maxAge: 25, // Retains last 25 states
      logOnly: environment.production // Restrict extension to log-only mode
    }),
    EffectsModule.forRoot(appStateEffects),

    TimeagoModule.forRoot({
      intl: TimeagoIntl,
      formatter: { provide: TimeagoFormatter, useClass: TimeagoCustomFormatter }
    }),
    TranslateModule.forRoot({
      missingTranslationHandler: {
        provide: MissingTranslationHandler,
        useClass: CustomMissingTranslationHandler
      },
      parser: {
        provide: TranslateParser,
        useClass: CustomTranslateParser
      },
      loader: {
        provide: TranslateLoader,
        useClass: LanguageLoader,
        deps: [HttpClient, JsonApiService]
      }
    }),

    // This app.
    AppRoutingModule,
    SharedModule.forRoot()
  ],
  providers: [CookieService, Title, WindowRefService],
  declarations: [AppComponent],
  bootstrap: [AppComponent]
})
export class AppModule {
  public constructor(iconLibrary: FaIconLibrary) {
    initFontAwesome(iconLibrary);
  }
}
