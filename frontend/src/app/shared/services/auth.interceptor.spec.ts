import { HTTP_INTERCEPTORS, HttpClientModule } from "@angular/common/http";
import { HttpClientTestingModule, HttpTestingController } from "@angular/common/http/testing";
import { TestBed } from "@angular/core/testing";
import { AppModule } from "@app/app.module";
import { AuthClassicApiService } from "@shared/services/api/classic/auth/auth-classic-api.service";
import { AuthInterceptor } from "@shared/services/auth.interceptor";
import { AuthService } from "@shared/services/auth.service";
import { MockBuilder, NG_MOCKS_INTERCEPTORS } from "ng-mocks";
import { CookieService } from "ngx-cookie-service";

describe(`AuthHttpInterceptor`, () => {
  let authService: AuthService;
  let authClassicApi: AuthClassicApiService;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await MockBuilder(AuthInterceptor, AppModule)
      .exclude(NG_MOCKS_INTERCEPTORS)
      .keep(HTTP_INTERCEPTORS)
      .replace(HttpClientModule, HttpClientTestingModule)
      .keep(AuthService)
      .keep(AuthClassicApiService)
      .mock(CookieService, {
        get: jest.fn().mockReturnValue("classic-auth-token")
      });

    authService = TestBed.inject(AuthService);
    authClassicApi = TestBed.inject(AuthClassicApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it("should add an Authorization header", () => {
    authService.login("handle", "password").subscribe(response => {
      expect(response).toBe(false);
    });

    const classicApiHttpRequest = httpMock.expectOne(`${authClassicApi.configUrl}/api-auth-token/`);
    expect(classicApiHttpRequest.request.headers.has("Authorization")).toEqual(true);
  });
});
