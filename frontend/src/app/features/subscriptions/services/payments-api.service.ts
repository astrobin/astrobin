import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { environment } from "@env/environment";
import { PayableProductInterface } from "@features/subscriptions/interfaces/payable-product.interface";
import { PaymentsApiCkeckoutSessionInterface } from "@features/subscriptions/interfaces/payments-api-ckeckout-session.interface";
import { PaymentsApiConfigInterface } from "@features/subscriptions/interfaces/payments-api-config.interface";
import { PricingInterface } from "@features/subscriptions/interfaces/pricing.interface";
import { Observable } from "rxjs";
import { map } from "rxjs/operators";

@Injectable({
  providedIn: "root"
})
export class PaymentsApiService {
  constructor(public readonly http: HttpClient) {}

  public getConfig(): Observable<PaymentsApiConfigInterface> {
    return this.http.get<PaymentsApiConfigInterface>(`${environment.classicApiUrl}/payments/config/`);
  }

  public createCheckoutSession(
    userId: number,
    product: PayableProductInterface,
    currency: string
  ): Observable<PaymentsApiCkeckoutSessionInterface> {
    return this.http.post<PaymentsApiCkeckoutSessionInterface>(
      `${environment.classicApiUrl}/payments/create-checkout-session/${userId}/${product}/${currency}/`,
      {}
    );
  }

  public getPrice(product: string, currency: string): Observable<PricingInterface> {
    return this.http.get<PricingInterface>(
      `${environment.classicApiUrl}/api/v2/payments/pricing/${product}/${currency}/`
    );
  }
}
