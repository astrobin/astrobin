import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IsProducerPipe } from "./is-producer.pipe";
import { IsRetailerPipe } from "./is-retailer.pipe";

@NgModule({
  declarations: [
    IsProducerPipe,
    IsRetailerPipe
  ],
  imports: [
    CommonModule
  ],
  exports: [
    IsProducerPipe,
    IsRetailerPipe
  ]
})
export class PipesModule { }
