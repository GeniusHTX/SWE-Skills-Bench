# Task: Implement a Notification System in Clojure for Metabase

## Background

Metabase (https://github.com/metabase/metabase) is built with a Clojure backend. This task requires implementing a notification dispatch system that sends alerts via multiple channels (email, Slack, webhook) when query results match configured conditions. The system uses Metabase's existing Toucan model layer and should follow Clojure idioms: data-oriented design, multimethods for dispatch, and REPL-driven development patterns.

## Files to Create/Modify

- `src/metabase/notification/core.clj` (create) — Core namespace: defines `Notification` record, multimethod `dispatch-notification` dispatching on channel type, and `process-notification` pipeline function.
- `src/metabase/notification/channels/email.clj` (create) — Email channel: formats notification as HTML email body, calls Metabase's email sending infrastructure.
- `src/metabase/notification/channels/slack.clj` (create) — Slack channel: formats notification as Slack Block Kit payload with sections for alert title, query results table, and action buttons.
- `src/metabase/notification/channels/webhook.clj` (create) — Webhook channel: POSTs JSON payload to a configured URL with HMAC-SHA256 signature for verification.
- `src/metabase/notification/conditions.clj` (create) — Condition evaluators: `rows-above-threshold`, `rows-below-threshold`, `column-value-changed`, `query-returns-results`. Each takes query results and returns a boolean + context map.
- `src/metabase/notification/scheduler.clj` (create) — Scheduler that checks pending notification rules, evaluates conditions, and dispatches notifications. Uses `core.async` for non-blocking processing.
- `test/metabase/notification/core_test.clj` (create) — Tests for notification dispatch, condition evaluation, and channel formatting.

## Requirements

### Notification Record

```clojure
(defrecord Notification [id alert-name channel-type channel-config
                         condition-type condition-params
                         query-results triggered-at])
```

### Multimethod Dispatch

```clojure
(defmulti dispatch-notification :channel-type)

(defmethod dispatch-notification :email [notification]
  ;; Format and send email
  )

(defmethod dispatch-notification :slack [notification]
  ;; Format and send Slack message
  )

(defmethod dispatch-notification :webhook [notification]
  ;; Format and POST webhook
  )
```

### Email Channel

- Formats HTML with: alert name as header, condition description, a results table (max 20 rows), and a link to the Metabase question.
- Subject: `"[Metabase Alert] {alert-name}"`.
- Uses Metabase's existing `metabase.email/send-message!` function.

### Slack Channel

- Builds Slack Block Kit payload:
  ```clojure
  {:blocks [{:type "header" :text {:type "plain_text" :text alert-name}}
            {:type "section" :text {:type "mrkdwn" :text condition-summary}}
            {:type "section" :fields (map format-column-value (take 10 rows))}
            {:type "actions" :elements [{:type "button" :text "View in Metabase" :url question-url}]}]}
  ```
- Truncates to fit Slack's block limits (50 blocks max, 3000 char per text field).

### Webhook Channel

- POSTs JSON to `channel-config.url` with headers:
  - `Content-Type: application/json`
  - `X-Metabase-Signature: HMAC-SHA256(secret, body)` where secret is from `channel-config.secret`.
  - `X-Metabase-Event: alert.triggered`
- Payload: `{:alert_name, :triggered_at, :condition, :results (first 100 rows), :question_url}`.
- Timeout: 10 seconds. On failure, log warning but do not retry (fire-and-forget).

### Condition Evaluators

- `(rows-above-threshold results {:threshold 100})` → true if row count > 100. Context: `{:row_count N}`.
- `(rows-below-threshold results {:threshold 10})` → true if row count < 10.
- `(column-value-changed results {:column "status" :previous-value "active"})` → true if the column contains a value different from `previous-value`.
- `(query-returns-results results {})` → true if results have at least 1 row.
- All return `{:triggered? boolean, :context map}`.

### Scheduler

- `(start-scheduler! interval-ms)` — starts a `core.async/go-loop` that periodically:
  1. Loads active notification rules from DB.
  2. Executes each rule's associated query.
  3. Evaluates the condition.
  4. If triggered, creates a `Notification` and dispatches it.
- `(stop-scheduler! scheduler)` — closes the async channel, stopping the loop.
- Concurrency: processes up to 5 notifications concurrently using `core.async/pipeline`.

### Expected Functionality

- A notification rule with `condition-type: :rows-above-threshold`, `threshold: 100`, and query returning 150 rows → triggers notification dispatch to the configured channel.
- Email dispatch sends an HTML email with 20-row table preview.
- Slack dispatch sends Block Kit payload with header, summary, field previews, and action button.
- Webhook dispatch POSTs signed JSON to the configured URL.
- Condition `column-value-changed` detects when a monitored column has new values.

## Acceptance Criteria

- `dispatch-notification` multimethod correctly routes to email, Slack, and webhook implementations.
- Email formats a valid HTML message with results table (max 20 rows).
- Slack payload follows Block Kit structure with proper truncation.
- Webhook includes HMAC-SHA256 signature in the `X-Metabase-Signature` header.
- All 4 condition evaluators return correct `{:triggered? :context}` maps.
- Scheduler uses `core.async` for non-blocking periodic processing with bounded concurrency.
- Tests verify: dispatch routing, email/slack/webhook formatting, condition evaluation, and HMAC signature computation.
