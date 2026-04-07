import type { APIRequestContext } from '@playwright/test';

type GraphqlResponse<TData> = {
  data?: TData;
  errors?: Array<{ message: string }>;
};

/**
 * Sends a GraphQL request and returns the typed `data` payload.
 * Throws on HTTP errors or GraphQL-level errors.
 */
export async function requestGraphql<TData>(
  api: APIRequestContext,
  query: string,
  variables: Record<string, unknown> = {},
): Promise<TData> {
  const response = await api.post('/api', {
    data: { query, variables },
  });

  if (!response.ok()) {
    throw new Error(`GraphQL request failed with status ${response.status()}`);
  }

  const body = (await response.json()) as GraphqlResponse<TData>;

  if (body.errors?.length) {
    throw new Error(body.errors.map((e) => e.message).join('; '));
  }

  if (!body.data) {
    throw new Error('GraphQL response did not include data');
  }

  return body.data;
}
