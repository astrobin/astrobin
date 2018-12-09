import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ApiModule } from "./api/api.module";
import { AppContextService } from "./app-context.service";
import { LegacyRoutesService } from "./legacy-routes.service";
import { UsersService } from "./users.service";

@NgModule({
  imports: [
    CommonModule,
    ApiModule
  ],
  providers: [
    AppContextService,
    LegacyRoutesService,
    UsersService,
  ],
  exports: [
    ApiModule
  ]
})
export class ServicesModule {
}
