import { HttpClient } from "@angular/common/http";
import { APP_INITIALIZER, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { FontAwesomeModule } from "@fortawesome/angular-fontawesome";
import { library as fontAwesomeLibrary } from "@fortawesome/fontawesome-svg-core";
import {
  faAsterisk,
  faBarcode,
  faBook,
  faBookmark,
  faChartBar,
  faImage,
  faUpload
} from "@fortawesome/free-solid-svg-icons";
import { NgbModule } from "@ng-bootstrap/ng-bootstrap";

import { TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { TranslateHttpLoader } from "@ngx-translate/http-loader";

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { LibraryModule } from "./library/library.module";
import { AppContextService } from "./library/services/app-context.service";
import { SharedModule } from "./library/shared.module";

// AoT requires an exported function for factories
export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http, './assets/i18n/', '.json');
}

export function appInitializer(appContext: AppContextService) {
  return () => appContext.load();
}

fontAwesomeLibrary.add(faAsterisk);
fontAwesomeLibrary.add(faBarcode);
fontAwesomeLibrary.add(faBook)
fontAwesomeLibrary.add(faBookmark);
fontAwesomeLibrary.add(faChartBar);
fontAwesomeLibrary.add(faImage);
fontAwesomeLibrary.add(faUpload);

@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    // Angular
    BrowserModule,

    // Third party
    FontAwesomeModule,
    NgbModule,
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [HttpClient]
      }
    }),

    // App
    AppRoutingModule,
    LibraryModule,
    SharedModule.forRoot()
  ],
  providers: [
    AppContextService,
    {
      provide: APP_INITIALIZER,
      useFactory: appInitializer,
      multi: true,
      deps: [
        AppContextService
      ]
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
