import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { NgbDropdownModule } from "@ng-bootstrap/ng-bootstrap";
import { PipesModule } from "../pipes/pipes.module";
import { SharedModule } from "../shared.module";
import { FooterComponent } from './footer/footer.component';
import { HeaderComponent } from "./header/header.component";

@NgModule({
  imports: [
    CommonModule,
    NgbDropdownModule,
    PipesModule,
    SharedModule
  ],
  declarations: [
    HeaderComponent,
    FooterComponent
  ],
  exports: [
    NgbDropdownModule,
    HeaderComponent,
    FooterComponent,
    PipesModule,
    SharedModule,
  ]
})
export class ComponentsModule { }
