import { HttpClient } from "@angular/common/http";
import { APP_INITIALIZER } from "@angular/core";
import { async, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { TranslateLoader, TranslateModule } from "@ngx-translate/core";
import { AppComponent } from './app.component';
import { appInitializer, HttpLoaderFactory } from "./app.module";
import { LibraryModule } from "./library/library.module";
import { AppContextService } from "./library/services/app-context.service";
import { SharedModule } from "./library/shared.module";

describe('AppComponent', () => {
  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [
        RouterTestingModule,
        LibraryModule,
        TranslateModule.forRoot({
          loader: {
            provide: TranslateLoader,
            useFactory: HttpLoaderFactory,
            deps: [HttpClient]
          }
        }),
        SharedModule,
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
      declarations: [
        AppComponent
      ],
    }).compileComponents();
  }));

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.debugElement.componentInstance;
    expect(app).toBeTruthy();
  });
});
