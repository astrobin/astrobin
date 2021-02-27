import { HTTP_INTERCEPTORS, HttpClientModule } from "@angular/common/http";
import { NgModule } from "@angular/core";
import { AuthInterceptor } from "../auth.interceptor";
import { AuthClassicApiService } from "./classic/auth/auth-classic-api.service";
import { CommonApiService } from "./classic/common/common-api.service";

@NgModule({
  imports: [HttpClientModule],
  providers: [
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true
    },
    AuthClassicApiService,
    CommonApiService
  ]
})
export class ApiModule {}
