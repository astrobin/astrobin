import { HttpClientModule } from "@angular/common/http";
import { NgModule } from '@angular/core';
import { CommonApiService } from "./common-api.service";

@NgModule({
  imports: [
    HttpClientModule
  ],
  providers: [
    CommonApiService
  ]
})
export class ApiModule {
}
